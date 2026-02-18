import miniaudio
import os
import numpy as np
import array
import platform

class MiniaudioPlayer:
    def __init__(self, file_path):
        """
        Simple audio player using miniaudio.
        Supports any format miniaudio supports (mp3, wav, flac, etc.)
        """
        self.file_path = file_path
        self._device = None
        self._stream = None
        self._paused = False
        self._running = False
        self._volume = 1.0 # 0.0 to 1.0
        self._nchannels = 2
        self._sample_rate = 44100
        self._frames_to_read = 1024
        self._duration_seconds = 0.0
        self._num_frames = 0
        self._position_frames = 0
        self._position_seconds = 0.0
        self._backend_name = "unknown"
        self._default_device_name = "unknown"
        self._load_file_info()

    @staticmethod
    def _preferred_backends():
        system = platform.system()
        if system == "Linux":
            return [miniaudio.Backend.PULSEAUDIO, miniaudio.Backend.ALSA, miniaudio.Backend.JACK]
        if system == "Darwin":
            return [miniaudio.Backend.COREAUDIO]
        if system == "Windows":
            return [miniaudio.Backend.WASAPI, miniaudio.Backend.DSOUND, miniaudio.Backend.WINMM]
        return []

    def _default_playback_device_id(self, backends):
        self._default_device_name = "system-default"
        try:
            devices = miniaudio.Devices(backends=backends)
            playbacks = devices.get_playbacks()
            for pb in playbacks or []:
                is_default = (
                    pb.get("is_default")
                    or pb.get("isDefault")
                    or pb.get("isDefaultDevice")
                    or pb.get("default")
                )
                if is_default:
                    self._default_device_name = str(pb.get("name", "system-default"))
                    return pb.get("id")
            if playbacks:
                # Keep OS-selected default device behavior; only expose first for diagnostics.
                self._default_device_name = f"system-default (enum first={playbacks[0].get('name', 'unknown')})"
        except Exception:
            self._default_device_name = "system-default"
        return None

    def _make_playback_device(self):
        backends = self._preferred_backends()
        self._default_playback_device_id(backends)
        device = miniaudio.PlaybackDevice(
            output_format=miniaudio.SampleFormat.SIGNED16,
            nchannels=self._nchannels,
            sample_rate=self._sample_rate,
            backends=backends,
            app_name="dj-blue-ai",
        )
        backend_name = str(getattr(device, "backend", "unknown")).lower()
        if backend_name == "null":
            raise RuntimeError("No usable audio backend (miniaudio NULL backend)")
        self._backend_name = backend_name
        return device

    def _load_file_info(self):
        try:
            info = miniaudio.get_file_info(self.file_path)
            self._duration_seconds = float(getattr(info, "duration", 0.0) or 0.0)
            self._num_frames = int(getattr(info, "num_frames", 0) or 0)
        except Exception:
            self._duration_seconds = 0.0
            self._num_frames = 0

    def start(self):
        """Starts or resumes playback."""
        if self._running and self._paused:
                self.resume()
                return True

        self.stop() # Ensure clean state

        if not os.path.exists(self.file_path):
            print(f"MiniaudioPlayer: File not found {self.file_path}")
            return False

        try:
            self._build_stream(seek_frame=0, seek_seconds=0.0)
            self._device = self._make_playback_device()
            self._device.start(self._stream)
            self._running = True
            self._paused = False
            print(
                f"MiniaudioPlayer: Playing {self.file_path} at volume {self._volume} "
                f"(backend={self._backend_name}, default_device={self._default_device_name})"
            )
            return True
        except Exception as e:
            print(f"MiniaudioPlayer Error: {e}")
            self._running = False
            return False

    def _build_stream(self, seek_frame: int, seek_seconds: float = 0.0):
        raw_stream = miniaudio.stream_file(
            self.file_path,
            nchannels=self._nchannels,
            sample_rate=self._sample_rate,
            frames_to_read=self._frames_to_read,
            seek_frame=max(0, int(seek_frame)),
        )
        self._position_frames = max(0, int(seek_frame))
        self._position_seconds = max(0.0, float(seek_seconds))
        self._stream = self._volume_generator(raw_stream)
        next(self._stream)

    def _volume_generator(self, stream):
        """Playback callback generator that honors requested frame sizes."""
        required_frames = yield b""

        while True:
            request = int(required_frames) if required_frames else self._frames_to_read
            try:
                chunk = stream.send(request)
            except StopIteration:
                self._running = False
                return

            if isinstance(chunk, array.array):
                sample_count = len(chunk)
                chunk_bytes = chunk.tobytes()
            else:
                chunk_bytes = bytes(chunk)
                sample_count = len(chunk_bytes) // 2  # int16

            frame_count = sample_count // self._nchannels
            self._position_frames += max(0, frame_count)
            self._position_seconds += max(0, frame_count) / float(self._sample_rate)

            if self._volume == 1.0:
                required_frames = yield chunk_bytes
                continue

            samples = np.frombuffer(chunk_bytes, dtype=np.int16).astype(np.float32)
            scaled = np.clip(samples * self._volume, -32768.0, 32767.0).astype(np.int16)
            required_frames = yield scaled.tobytes()

    def set_volume(self, volume):
        """Sets the volume (0.0 to 1.0)."""
        self._volume = max(0.0, min(1.0, float(volume)))
        # Note: If already playing, the generator will pick up the new value 
        # on the next chunk because it accesses self._volume in each iteration.

    def pause(self):
        """Pauses playback."""
        if self._device and self._running and not self._paused:
            # Stopping the device stops consuming the stream.
            # The stream generator state is preserved in Python.
            self._device.stop() 
            self._paused = True
            print("MiniaudioPlayer: Paused")

    def resume(self):
        """Resumes playback from pause."""
        if self._device and self._running and self._paused:
            self._device.start(self._stream)
            self._paused = False
            print("MiniaudioPlayer: Resumed")

    def stop(self):
        """Stops playback and resets state."""
        if self._device:
            self._device.close() # Closes the device and stops playback
        self._device = None
        self._stream = None
        self._running = False
        self._paused = False
        self._position_frames = 0
        self._position_seconds = 0.0

    def close(self):
        """Cleanup."""
        self.stop()
    
    @property
    def paused(self):
        return self._paused

    def is_playing(self):
        return self._running and not self._paused

    def duration_seconds(self) -> float:
        return self._duration_seconds

    def position_seconds(self) -> float:
        return max(0.0, self._position_seconds)

    def seek(self, seconds: float):
        if not os.path.exists(self.file_path):
            return False

        target_seconds = max(0.0, float(seconds))
        if self._duration_seconds > 0:
            target_seconds = min(target_seconds, self._duration_seconds)
        if self._duration_seconds > 0 and self._num_frames > 0:
            ratio = target_seconds / self._duration_seconds
            target_frame = int(max(0.0, min(1.0, ratio)) * self._num_frames)
        else:
            target_frame = int(target_seconds * self._sample_rate)

        was_playing = self._running and not self._paused
        was_running = self._running

        try:
            if self._device:
                try:
                    self._device.stop()
                except Exception:
                    pass
                self._device.close()
                self._device = None

            self._build_stream(seek_frame=target_frame, seek_seconds=target_seconds)
            self._device = self._make_playback_device()

            if was_playing:
                self._device.start(self._stream)
                self._paused = False
                self._running = True
            elif was_running:
                self._paused = True
                self._running = True
            else:
                self._paused = True
                self._running = False
            print(
                f"MiniaudioPlayer: Seek -> {target_seconds:.2f}s "
                f"(backend={self._backend_name}, default_device={self._default_device_name})"
            )
            return True
        except Exception as e:
            print(f"MiniaudioPlayer seek error: {e}")
            self._device = None
            self._running = False
            self._paused = False
            return False
