from typing import Optional, List, Tuple
from pathlib import Path
from array import array
from io import BytesIO
import subprocess
import threading
import pyaudio
import audioop
import select
import struct
import wave
import time
import math
from architects.helpers.record_live_mix_linux import LiveMixer, RATE, CHANNELS

_USE_EXISTING_DURATION = object()


class PlaybackController:
    def __init__(self, wav_bytes_io, chunk=1024):
        self.p = pyaudio.PyAudio()
        self.wf = wave.open(wav_bytes_io, "rb")
        self.stream = None
        self.paused = False
        self.chunk = chunk

    def _cb(self, in_data, frame_count, time_info, status):
        if self.paused:
            # return silence (same size as real audio frame)
            frame_bytes = self.wf.getsampwidth() * self.wf.getnchannels()
            return (b"\x00" * (frame_count * frame_bytes), pyaudio.paContinue)

        data = self.wf.readframes(frame_count)
        if not data:
            return (data, pyaudio.paComplete)
        return (data, pyaudio.paContinue)

    def start(self):
        if self.stream is None:
            self.stream = self.p.open(
                format=self.p.get_format_from_width(self.wf.getsampwidth()),
                channels=self.wf.getnchannels(),
                rate=self.wf.getframerate(),
                output=True,
                frames_per_buffer=self.chunk,
                stream_callback=self._cb,
            )
        self.paused = False
        self.stream.start_stream()

    def pause(self):
        self.paused = True

    def resume(self):
        self.paused = False

    def wait(self):
        while self.stream.is_active():
            pass

    def stop(self):
        self.paused = True
        self.stream.stop_stream()
        self.stream.close()
        self.stream = None
        self.wf.rewind()

    def close(self):
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        self.wf.close()
        self.p.terminate()


class RecordingController:
    def __init__(self, rate=44100, chunk=1024, channels=1, sampwidth=2):
        self.p = pyaudio.PyAudio()
        self.rate = rate
        self.chunk = chunk
        self.channels = channels
        self.sampwidth = sampwidth

        self.stream = None
        self.paused = False
        self.stopped = False

        self.buffer = bytearray()
        self.chunks = []

    def _cb(self, in_data, frame_count, time_info, status):
        if not self.paused and not self.stopped:
            self.chunks.append(in_data)
        return (None, pyaudio.paContinue)
    
    def get_pcm(self):
        return b''.join(self.chunks)

    def start(self):
        if self.stream is None:
            self.stream = self.p.open(
                format=pyaudio.paInt16,
                channels=self.channels,
                rate=self.rate,
                input=True,
                stream_callback=self._cb,
                frames_per_buffer=self.chunk,
            )
        self.paused = False
        self.stopped = False
        self.stream.start_stream()

    def pause(self):
        self.paused = True

    def resume(self):
        self.paused = False

    def wait(self):
        while self.stream.is_active():
            pass

    def stop(self):
        self.paused = True
        self.stopped = True
        self.stream.stop_stream()
        self.stream.close()
        self.stream = None

    def close(self):
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        self.p.terminate()


class PlaybackRecorderLinux:
    def __init__(self, duration=None, rate=44100, channels=2, sampwidth=2, monitor=None):
        """
        Linux-only playback recorder using PulseAudio 'parec'.
        Works with PipeWire or PulseAudio.
        Records in timed chunks and stops early if .stop() is called.
        Default duration is unlimited; pass a value to clamp runtime.
        """
        self.rate = rate
        self.channels = channels
        self.sampwidth = sampwidth

        self.monitor = monitor or self.get_default_monitor_linux()
        self.proc = None
        self.thread = None

        self.chunks = []
        self.paused = False
        self.stopped = False
        self.duration = duration

    @staticmethod
    def get_default_monitor_linux():
        default_sink = subprocess.check_output(
            ["pactl", "get-default-sink"], text=True
        ).strip()
        return default_sink + ".monitor"

    def _reader(self):
        frame_bytes = self.sampwidth * self.channels
        chunk_bytes = 1024 * frame_bytes

        target_frames = None if self.duration is None else int(self.rate * self.duration)
        deadline = None if self.duration is None else time.monotonic() + self.duration

        frames_written = 0
        stdout = self.proc.stdout

        while not self.stopped:
            if target_frames is not None and frames_written >= target_frames:
                break

            max_bytes = chunk_bytes
            if target_frames is not None:
                remaining_frames = target_frames - frames_written
                max_bytes = min(chunk_bytes, remaining_frames * frame_bytes)

            timeout = 0.5 if deadline is None else max(0.0, min(0.5, deadline - time.monotonic()))
            ready, _, _ = select.select([stdout], [], [], timeout)
            if not ready:
                continue

            raw = stdout.read(max_bytes)
            if not raw:
                break

            if not self.paused:
                self.chunks.append(raw)
                frames_written += len(raw) // frame_bytes

        # Pad to requested duration if we ran short to make length explicit.
        if target_frames is not None and frames_written < target_frames:
            missing_frames = target_frames - frames_written
            self.chunks.append(b"\x00" * missing_frames * frame_bytes)

        # force stop when duration hit or parent requested stop
        self.stop()

    def start(self, duration=_USE_EXISTING_DURATION):
        """
        duration = seconds to record (None = unlimited)
        """
        if duration is not _USE_EXISTING_DURATION:
            self.duration = duration
        self.stopped = False
        self.paused = False
        self.chunks = []

        self.proc = subprocess.Popen(
            [
                "parec",
                "-d", self.monitor,
                "--raw",
                "--rate", str(self.rate),
                "--channels", str(self.channels),
                "--format", "s16le",
                "--latency-msec", "5",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )

        self.thread = threading.Thread(target=self._reader, daemon=True)
        self.thread.start()

    def pause(self):
        self.paused = True

    def resume(self):
        self.paused = False

    def stop(self):
        self.paused = True
        self.stopped = True

        if self.proc:
            try:
                self.proc.terminate()
            except ProcessLookupError:
                pass
            self.proc = None

        # Only join if this is NOT the reader thread
        if self.thread and threading.current_thread() is not self.thread:
            self.thread.join(timeout=0.05)

        self.thread = None

    def get_pcm(self):
        return b"".join(self.chunks)

    def close(self):
        # Stop capture and clean up the subprocess/thread if still active.
        self.stop()
        self.proc = None
        self.thread = None


class MultiPlaybackRecorder:
    """
    Manages multiple PlaybackRecorderLinux instances and mixes their output.
    Used when multiple source monitors are selected.
    """
    def __init__(self, monitors: List[str], rate=44100, channels=2, sampwidth=2):
        self.recorders = [
            PlaybackRecorderLinux(monitor=m, rate=rate, channels=channels, sampwidth=sampwidth) 
            for m in monitors
        ]
        self.chunks = []
        self.paused = False
        self.stopped = False
        self.rate = rate
        self.channels = channels
        self.sampwidth = sampwidth
        
        self._mixer_thread = None
        self._mixer_active = False

    def start(self, duration=None):
        for rec in self.recorders:
            rec.start(duration)
            
        self.chunks = []
        self.stopped = False
        self.paused = False
        self._mixer_active = True
        
        self._mixer_thread = threading.Thread(target=self._mixer_loop, daemon=True)
        self._mixer_thread.start()

    def _mixer_loop(self):
        while self._mixer_active and not self.stopped:
            # Find the minimum number of chunks available across all recorders
            # We can only mix up to the point where all recorders have data
            if not self.recorders:
                break
                
            min_len = min(len(r.chunks) for r in self.recorders)
            current_processed = len(self.chunks)
            
            if min_len > current_processed:
                for i in range(current_processed, min_len):
                    # Start with the first recorder's chunk
                    mixed_chunk = self.recorders[0].chunks[i]
                    
                    # Add remaining recorders
                    for rec in self.recorders[1:]:
                        chunk_to_add = rec.chunks[i]
                        
                        # Ensure lengths match before mixing (though they should be consistent from parec)
                        len_a = len(mixed_chunk)
                        len_b = len(chunk_to_add)
                        if len_a != len_b:
                            common = min(len_a, len_b)
                            mixed_chunk = mixed_chunk[:common]
                            chunk_to_add = chunk_to_add[:common]
                            
                        mixed_chunk = audioop.add(mixed_chunk, chunk_to_add, self.sampwidth)
                        
                    self.chunks.append(mixed_chunk)
            
            time.sleep(0.01)

    def pause(self):
        self.paused = True
        for r in self.recorders:
            r.pause()

    def resume(self):
        self.paused = False
        for r in self.recorders:
            r.resume()

    def stop(self):
        self.stopped = True
        self._mixer_active = False
        for r in self.recorders:
            r.stop()
        if self._mixer_thread:
            self._mixer_thread.join()

    def get_pcm(self):
        return b"".join(self.chunks)

    def close(self):
        self.stop()
        for r in self.recorders:
            r.close()


class AudioController:
    """
    Orchestrates mic + speaker recording in fixed chunks.
    Starts speaker first, then mic, keeps streams open, and stores
    chunk pairs in the order they are produced.
    """

    def __init__(
        self,
        *,
        chunk_seconds: int = 30,
        monitor: Optional[str] = None,
        monitors: Optional[List[str]] = None,
        rate: int = 44100,
        mic_channels: int = 1,
        speaker_channels: int = 2,
        mic_chunk: int = 1024,
    ):
        self.chunk_seconds = chunk_seconds

        self.mic = RecordingController(rate=rate, chunk=mic_chunk, channels=mic_channels)
        
        if monitors and len(monitors) > 0:
            self.speaker = MultiPlaybackRecorder(
                monitors=monitors,
                rate=rate,
                channels=speaker_channels,
                sampwidth=2
            )
        else:
            self.speaker = PlaybackRecorderLinux(
                duration=None,  # keep open until stopped
                rate=rate,
                channels=speaker_channels,
                sampwidth=2,
                monitor=monitor,
            )

        self._chunks: List[Tuple[bytes, bytes]] = []
        self._stop_event = threading.Event()
        self._chunk_thread: Optional[threading.Thread] = None
        self._last_mic_idx = 0
        self._last_spk_idx = 0
        self._started = False

    @property
    def chunks(self) -> List[Tuple[bytes, bytes]]:
        return self._chunks

    def start(self):
        if self._started:
            return
        self._stop_event.clear()
        self._last_mic_idx = 0
        self._last_spk_idx = 0
        self._chunks.clear()

        # Order matters: start speaker capture before mic.
        self.speaker.start(duration=None)
        self.mic.start()

        self._chunk_thread = threading.Thread(target=self._chunk_loop, daemon=True)
        self._chunk_thread.start()
        self._started = True

    def _chunk_loop(self):
        while not self._stop_event.wait(self.chunk_seconds):
            self._collect_chunk(force=False)

    def _collect_chunk(self, *, force: bool):
        mic_new = self.mic.chunks[self._last_mic_idx :]
        spk_new = self.speaker.chunks[self._last_spk_idx :]

        self._last_mic_idx += len(mic_new)
        self._last_spk_idx += len(spk_new)

        mic_pcm = b"".join(mic_new)
        spk_pcm = b"".join(spk_new)

        if mic_pcm or spk_pcm or force:
            self._chunks.append((mic_pcm, spk_pcm))

    def pause(self):
        self.mic.pause()
        self.speaker.pause()

    def resume(self):
        self.mic.resume()
        self.speaker.resume()

    def stop(self):
        if not self._started:
            return
        self._stop_event.set()
        if self._chunk_thread:
            self._chunk_thread.join()
        # Grab any trailing partial chunk.
        self._collect_chunk(force=True)

        self.mic.stop()
        self.speaker.stop()
        self._started = False

    def wait(self):
        if self._chunk_thread:
            self._chunk_thread.join()

    def close(self):
        self.mic.close()
        self.speaker.close()

    def pop_chunk(self) -> Optional[Tuple[bytes, bytes]]:
        if not self._chunks:
            return None
        return self._chunks.pop(0)

    def _combine_to_dual_channel(self, mic_pcm: bytes, spk_pcm: bytes) -> Optional[bytes]:
        """
        Combine mic (mono) and speaker (stereo/mono) into a 2-channel 16-bit stream:
        channel 0 = mic, channel 1 = speaker downmixed to mono.
        """
        if self.mic.sampwidth != 2 or self.speaker.sampwidth != 2:
            return None  # only 16-bit supported here
        if self.mic.rate != self.speaker.rate:
            return None  # mismatch in rates

        mic_samples = array("h")
        mic_samples.frombytes(mic_pcm)

        spk_samples = array("h")
        spk_samples.frombytes(spk_pcm)

        # Downmix speaker to mono if stereo
        if self.speaker.channels == 2:
            spk_mono = array("h")
            for i in range(0, len(spk_samples), 2):
                left = spk_samples[i]
                right = spk_samples[i + 1] if i + 1 < len(spk_samples) else 0
                spk_mono.append((left + right) // 2)
            spk_samples = spk_mono

        max_frames = max(len(mic_samples), len(spk_samples))
        if len(mic_samples) < max_frames:
            mic_samples.extend([0] * (max_frames - len(mic_samples)))
        if len(spk_samples) < max_frames:
            spk_samples.extend([0] * (max_frames - len(spk_samples)))

        out = array("h")
        for i in range(max_frames):
            out.append(mic_samples[i])
            out.append(spk_samples[i])
        return out.tobytes()

    def _combine_stereo_mix(self, mic_pcm: bytes, spk_pcm: bytes) -> Optional[bytes]:
        """
        Mix mic (mono -> stereo) with speaker stereo into stereo 16-bit.
        Keeps speaker stereo intact and adds mic equally to L/R with clipping.
        """
        if self.mic.sampwidth != 2 or self.speaker.sampwidth != 2:
            return None
        if self.mic.rate != self.speaker.rate:
            return None

        def to_stereo(samples: array, channels: int) -> tuple[array, array]:
            if channels == 1:
                return samples, samples
            left = array("h", samples[0::2])
            right = array("h", samples[1::2])
            return left, right

        mic_samples = array("h"); mic_samples.frombytes(mic_pcm)
        spk_samples = array("h"); spk_samples.frombytes(spk_pcm)

        mic_l, mic_r = to_stereo(mic_samples, 1)
        spk_l, spk_r = to_stereo(spk_samples, self.speaker.channels)

        max_frames = max(len(spk_l), len(spk_r), len(mic_l), len(mic_r))
        def pad(arr, target):
            if len(arr) < target:
                arr.extend([0] * (target - len(arr)))
            return arr
        mic_l = pad(mic_l, max_frames); mic_r = pad(mic_r, max_frames)
        spk_l = pad(spk_l, max_frames); spk_r = pad(spk_r, max_frames)

        out = array("h")
        for i in range(max_frames):
            # simple mix with clipping
            l = spk_l[i] + mic_l[i]
            r = spk_r[i] + mic_r[i]
            l = max(-32768, min(32767, l))
            r = max(-32768, min(32767, r))
            out.append(l); out.append(r)
        return out.tobytes()

    def pop_combined_dual(self) -> Optional[bytes]:
        """
        Pop one chunk and return a combined 2-channel (mic, speaker-mono) PCM blob.
        """
        chunk = self.pop_chunk()
        if chunk is None:
            return None
        mic_chunk, spk_chunk = chunk
        return self._combine_to_dual_channel(mic_chunk, spk_chunk)

    def pop_combined_stereo(self) -> Optional[bytes]:
        """
        Pop one chunk and return a stereo mix: speaker stereo intact + mic mirrored to L/R.
        """
        chunk = self.pop_chunk()
        if chunk is None:
            return None
        mic_chunk, spk_chunk = chunk
        return self._combine_stereo_mix(mic_chunk, spk_chunk)


class LiveMixerController:
    """
    Linux-only controller using the LiveMixer for dynamic app/mic discovery and mixing.
    Follows a similar interface to AudioController for compatibility.
    """
    def __init__(self, chunk_seconds: int = 30, rate: int = RATE, channels: int = CHANNELS, blacklist: Optional[List[str]] = None):
        self.chunk_seconds = chunk_seconds
        self.rate = rate
        self.channels = channels
        self.sampwidth = 2
        self.blacklist = blacklist
        
        self.mixer = None
        self._chunks: List[bytes] = []
        self._stop_event = threading.Event()
        self._chunk_thread: Optional[threading.Thread] = None
        self._started = False

    def start(self):
        if self._started:
            return
        self.mixer = LiveMixer(blacklist=self.blacklist)
        self._stop_event.clear()
        self._chunks.clear()
        
        self._chunk_thread = threading.Thread(target=self._chunk_loop, daemon=True)
        self._chunk_thread.start()
        self._started = True

    def _chunk_loop(self):
        while not self._stop_event.wait(self.chunk_seconds):
            pcm = self.mixer.pop_buffer()
            if pcm:
                self._chunks.append(pcm)

    def stop(self):
        if not self._started:
            return
        self._stop_event.set()
        if self._chunk_thread:
            self._chunk_thread.join()
            
        # Final pop
        if self.mixer:
            pcm = self.mixer.pop_buffer()
            if pcm:
                self._chunks.append(pcm)
            self.mixer.stop()
            
        self._started = False

    def close(self):
        self.stop()
        self.mixer = None

    def pop_combined_stereo(self) -> Optional[bytes]:
        if not self._chunks:
            return None
        return self._chunks.pop(0)

    @property
    def mic(self):
        # Mock mic object for compatibility with TranscriptionManager's rate/sampwidth access
        class MockMic:
            def __init__(self, rate, sampwidth):
                self.rate = rate
                self.sampwidth = sampwidth
        return MockMic(self.rate, self.sampwidth)


# Network requests packet controller/scheduler
class SoundPacketBuilder:
    def __init__(self, audio_bytes: bytes, *, rate: int, channels: int = 2, sampwidth: int = 2):
        self.orig_rate = rate
        self.channels = channels
        self.sampwidth = sampwidth

        self.new_rate = 16000
        self.packet = audio_bytes
        self.encoding = "pcm16"

    def new_pck(self, audio_bytes: bytes, rate: int, channels: int = 2, sampwidth: int = 2):
        pass

    def prep_pck(self) -> bytes:
        """
        Prepare audio bytes for network / AI transport.
        Output: μ-law, mono, 16kHz
        """
        self._ensure_mono()
        self._resample()
        self._compress()
        return self.packet

    def _ensure_mono(self):
        if self.channels == 1:
            return

        # Downmix to mono (simple average)
        self.packet = audioop.tomono(
            self.packet,
            self.sampwidth,
            0.5,
            0.5,
        )
        self.channels = 1

    def _resample(self):
        if self.orig_rate == self.new_rate:
            return

        # audioop.ratecv returns (data, state)
        self.packet, _ = audioop.ratecv(
            self.packet,
            self.sampwidth,
            self.channels,
            self.orig_rate,
            self.new_rate,
            None,
        )

    def _compress(self):
        # PCM16 → μ-law (8-bit)
        self.packet = audioop.lin2ulaw(self.packet, self.sampwidth)
        self.encoding = "mulaw"

    def write(self, path: str, *, decoded_wav: bool = False):
        """
        Save packet to disk.

        decoded_wav=False  -> saves raw compressed bytes (.ulaw)
        decoded_wav=True   -> saves decoded PCM WAV for listening
        """
        if self.encoding != "mulaw":
            raise RuntimeError("packet is not compressed")

        if decoded_wav:
            pcm = audioop.ulaw2lin(self.packet, 2)
            with wave.open(path, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(self.new_rate)
                wf.writeframes(pcm)
        else:
            with open(path, "wb") as f:
                f.write(self.packet)



def write_wav(path, pcm, *, rate, channels, sampwidth):
    with wave.open(path, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sampwidth)
        wf.setframerate(rate)
        wf.writeframes(pcm)


def read_wav(path):
    with wave.open(path, "rb") as wf:
        channels = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        rate = wf.getframerate()
        data = wf.readframes(wf.getnframes())
    return data, {"channels": channels, "sampwidth": sampwidth, "rate": rate}


def audio_bytes_info(
    audio_bytes: bytes,
    sample_rate: int,
    channels: int = 1,
    sample_width: int = 2,  # bytes (2 = int16)
):
    if not audio_bytes:
        raise ValueError("empty audio buffer")

    total_bytes = len(audio_bytes)
    frame_size = channels * sample_width
    total_frames = total_bytes // frame_size
    duration_sec = total_frames / sample_rate

    # RMS + peak (int16 only)
    rms = peak = None
    if sample_width == 2:
        samples = struct.unpack(
            "<" + "h" * (total_bytes // 2), audio_bytes
        )
        sq = sum(s * s for s in samples)
        rms = math.sqrt(sq / len(samples))
        peak = max(abs(s) for s in samples)

    print(f"bytes        : {total_bytes}")
    print(f"frames       : {total_frames}")
    print(f"duration (s) : {duration_sec:.4f}")
    print(f"sample_rate  : {sample_rate}")
    print(f"channels     : {channels}")
    print(f"sample_width : {sample_width} bytes")

    if rms is not None:
        print(f"rms          : {rms:.1f}")
        print(f"peak         : {peak}")

    return {
        "bytes": total_bytes,
        "frames": total_frames,
        "duration_sec": duration_sec,
        "sample_rate": sample_rate,
        "channels": channels,
        "sample_width": sample_width,
        "rms": rms,
        "peak": peak,
    }


def pcm_to_wav_bytes(pcm: bytes, *, rate: int, channels: int, sampwidth: int) -> bytes:
    """
    Convert raw PCM bytes to a WAV file in memory (bytes).
    """
    buf = BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sampwidth)
        wf.setframerate(rate)
        wf.writeframes(pcm)
    return buf.getvalue()


if __name__ == "__main__":
    AUDIO_PATH = Path(__file__).with_name("out.wav")
    wav_bytes = open(AUDIO_PATH, "rb").read()

    play_con = PlaybackController(BytesIO(wav_bytes))
    expected_duration = play_con.wf.getnframes() / play_con.wf.getframerate()
    controller = AudioController(chunk_seconds=30)

    controller.start()
    play_con.start()

    play_con.wait()

    controller.stop()

    play_con.close()
    controller.close()

    print("frames:", play_con.wf.getnframes())
    print("rate:", play_con.wf.getframerate())
    print("duration:", expected_duration)

    def pcm_seconds(raw, rate, channels, sampwidth):
        if not raw:
            return 0.0
        return len(raw) / (rate * channels * sampwidth)

    all_mic = b"".join(chunk[0] for chunk in controller.chunks)
    all_spk = b"".join(chunk[1] for chunk in controller.chunks)

    print("mic seconds (computed):", pcm_seconds(all_mic, controller.mic.rate, controller.mic.channels, controller.mic.sampwidth))
    print("speaker seconds (computed):", pcm_seconds(all_spk, controller.speaker.rate, controller.speaker.channels, controller.speaker.sampwidth))

    audio_bytes_info(all_mic, controller.mic.rate)
    audio_bytes_info(all_spk, controller.speaker.rate)

    prep = SoundPacketBuilder(all_spk, rate=44100)
    prep.prep_pck()
    prep.write("audio.ulaw")

    ulaw = open("audio.ulaw", "rb").read()
    pcm = audioop.ulaw2lin(ulaw, 2)

    with wave.open("decoded.wav", "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        wf.writeframes(pcm)

    # BASE_DIR = Path(__file__).resolve().parent

    # MIC_PATH = BASE_DIR / "mic.wav"
    # SPEAKER_REC_PATH = BASE_DIR / "playback.wav"
    # TEST_PATH = BASE_DIR / "test.wav"

    # with wave.open(str(MIC_PATH), "wb") as wf:
    #     wf.setnchannels(controller.mic.channels)
    #     wf.setsampwidth(controller.mic.sampwidth)
    #     wf.setframerate(controller.mic.rate)
    #     wf.writeframes(all_mic)

    # with wave.open(str(SPEAKER_REC_PATH), "wb") as wf:
    #     wf.setnchannels(controller.speaker.channels)
    #     wf.setsampwidth(controller.speaker.sampwidth)
    #     wf.setframerate(controller.speaker.rate)
    #     wf.writeframes(all_spk)

    # # Example usage: pop and persist the next chunk pair.
    # popped_pair = controller.pop_chunk()
    # if popped_pair:
    #     mic_chunk, spk_chunk = popped_pair
    #     print("popped chunk lens:", len(mic_chunk), len(spk_chunk))
    #     write_wav(str(BASE_DIR / "chunk_mic.wav"), mic_chunk,
    #             rate=controller.mic.rate,
    #             channels=controller.mic.channels,
    #             sampwidth=controller.mic.sampwidth)
    #     write_wav(str(BASE_DIR / "chunk_spk.wav"), spk_chunk,
    #             rate=controller.speaker.rate,
    #             channels=controller.speaker.channels,
    #             sampwidth=controller.speaker.sampwidth)

    # # Example usage: combined dual-channel (mic left, speaker-mono right).
    # popped_combined_dual = controller.pop_combined_dual()
    # if popped_combined_dual:
    #     write_wav(str(BASE_DIR / "chunk_combined_dual.wav"), popped_combined_dual,
    #             rate=controller.mic.rate,
    #             channels=2,
    #             sampwidth=controller.mic.sampwidth)

    # # Example usage: combined stereo mix (speaker stereo intact + mic mirrored to L/R).
    # popped_combined_stereo = controller.pop_combined_stereo()
    # if popped_combined_stereo:
    #     write_wav(str(BASE_DIR / "chunk_combined_stereo.wav"), popped_combined_stereo,
    #             rate=controller.mic.rate,
    #             channels=2,
    #             sampwidth=controller.mic.sampwidth)
