import sys
import time
import subprocess
import threading
from typing import Optional, List
import numpy as np
import pulsectl
import collections
import wave
import signal
import os

# Configuration
RATE = 48000
CHANNELS = 2
CHUNK_MS = 20 # 20ms chunks for low latency mixing
CHUNK_SIZE = int(RATE * CHUNK_MS / 1000)
DTYPE = np.int16

class AudioSource:
    def __init__(self, serial, name, is_mic=False):
        self.serial = serial
        self.name = name
        self.is_mic = is_mic
        self.active = True
        self.lock = threading.Lock()
        self.buffer = collections.deque() # Queue of numpy arrays
        
        # Start pw-record
        # We force 2 channels so PipeWire handles upmixing mono mics
        cmd = [
            "pw-record", 
            "--target", str(serial), 
            "--format", "s16", 
            "--rate", str(RATE), 
            "--channels", str(CHANNELS), 
            "--latency", f"{CHUNK_MS}ms", 
            "-"
        ]
        
        self.proc = subprocess.Popen(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.DEVNULL, 
            bufsize=4096 * 10
        )
        self.thread = threading.Thread(target=self._reader, daemon=True)
        self.thread.start()

    def _reader(self):
        bytes_per_sample = 2 * CHANNELS
        chunk_bytes = CHUNK_SIZE * bytes_per_sample
        
        while self.active:
            try:
                # Blocking read ensures we wait for data
                raw = self.proc.stdout.read(chunk_bytes)
                if not raw: break
                
                # Align data if we got a partial read
                if len(raw) % bytes_per_sample != 0:
                    raw = raw[:-(len(raw) % bytes_per_sample)]
                
                if len(raw) == 0: continue

                # Convert to numpy
                data = np.frombuffer(raw, dtype=DTYPE).reshape(-1, CHANNELS)
                
                with self.lock:
                    self.buffer.append(data)
            except Exception:
                break
        self.active = False

    def pop_chunk(self):
        """Return the next chunk from this source, or None if buffer empty."""
        with self.lock:
            if self.buffer:
                return self.buffer.popleft()
        return None

    def stop(self):
        self.active = False
        if self.proc:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=0.5)
            except:
                self.proc.kill()

class LiveMixer:
    def __init__(self, blacklist: Optional[List[str]] = None):
        self.sources = {} # Key: Serial/ID -> AudioSource
        self.pulse = pulsectl.Pulse('live-mixer')
        self.mix_buffer = [] # Accumulation list of numpy arrays
        self.buffer_lock = threading.Lock()
        self.running = True
        
        if blacklist is not None:
            self.blacklist = blacklist
        else:
            self.blacklist = ['pw-record', 'live-mixer', 'easyeffects', 'loopback', 'speech-dispatcher', 'python']
        
        # Start Mixer Thread
        self.thread = threading.Thread(target=self._mix_loop, daemon=True)
        self.thread.start()

    def _mix_loop(self):
        while self.running:
            start_time = time.time()
            self._update_sources()
            
            # Prepare a blank chunk for this time slice
            # Use int32 for mixing headroom
            mixed_chunk = np.zeros((CHUNK_SIZE, CHANNELS), dtype=np.int32)
            active_count = 0
            
            # Iterate copy of sources
            current_sources = list(self.sources.values())
            
            for src in current_sources:
                chunk = src.pop_chunk()
                if chunk is not None:
                    # If chunk is smaller/larger than expected (shouldn't happen often due to fixed read), handle it
                    l = min(len(chunk), len(mixed_chunk))
                    mixed_chunk[:l] += chunk[:l]
                    active_count += 1
            
            # If we processed valid audio, append to buffer
            # If silence, we still append silence to keep time continuity? 
            # Yes, otherwise "popping" 10s later would result in 0s audio file.
            
            # Clip and convert back to int16
            np.clip(mixed_chunk, -32768, 32767, out=mixed_chunk)
            final_chunk = mixed_chunk.astype(np.int16)
            
            with self.buffer_lock:
                self.mix_buffer.append(final_chunk)
            
            # Maintain timing
            # If processing took less than chunk time, sleep remainder
            elapsed = time.time() - start_time
            sleep_time = (CHUNK_MS / 1000.0) - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)

    def _update_sources(self):
        # 1. Apps (Sink Inputs)
        try:
            sink_inputs = self.pulse.sink_input_list()
        except: return
        
        # 2. Mic (Default Source)
        try:
            server_info = self.pulse.server_info()
            default_source_name = server_info.default_source_name
            source_list = self.pulse.source_list()
            mic_source = next((s for s in source_list if s.name == default_source_name), None)
        except: mic_source = None

        seen_keys = set()

        # Update Apps
        for si in sink_inputs:
            serial = si.index
            key = f"app_{serial}"
            seen_keys.add(key)
            
            if key not in self.sources:
                name = si.proplist.get('application.name', 'unknown')
                media_name = si.proplist.get('media.name', '')
                
                # Check blacklist
                full_name = (name + " " + media_name).lower()
                if any(b in full_name for b in self.blacklist): 
                    continue
                
                print(f"[+] Added App: {name} ({serial})")
                self.sources[key] = AudioSource(serial, name)

        # Update Mic
        if mic_source:
            key = f"mic_{mic_source.index}"
            seen_keys.add(key)
            if key not in self.sources:
                print(f"[+] Added Mic: {mic_source.description}")
                self.sources[key] = AudioSource(mic_source.index, "Microphone", is_mic=True)

        # Cleanup removed sources
        for key in list(self.sources.keys()):
            if key not in seen_keys:
                print(f"[-] Removed: {self.sources[key].name}")
                self.sources[key].stop()
                del self.sources[key]

    def pop_buffer(self):
        """
        Returns all accumulated audio bytes and clears the buffer.
        Returns empty bytes if buffer is empty.
        """
        with self.buffer_lock:
            if not self.mix_buffer:
                return b""
            
            # Concatenate all chunks
            combined = np.concatenate(self.mix_buffer)
            self.mix_buffer.clear()
            return combined.tobytes()

    def stop(self):
        self.running = False
        for s in self.sources.values():
            s.stop()

# --- Example Usage ---
def main():
    mixer = LiveMixer()
    print("Live Mixer Started.")
    print("Recording... (Will pop buffer every 5 seconds)")
    
    try:
        count = 1
        while True:
            time.sleep(5)
            
            # Pop audio!
            pcm_data = mixer.pop_buffer()
            
            if len(pcm_data) > 0:
                filename = f"output_part_{count}.wav"
                print(f"[*] Popped {len(pcm_data)} bytes -> {filename}")
                
                with wave.open(filename, 'wb') as wf:
                    wf.setnchannels(CHANNELS)
                    wf.setsampwidth(2) # 16-bit
                    wf.setframerate(RATE)
                    wf.writeframes(pcm_data)
                
                count += 1
            else:
                print("[*] Buffer empty (Silence?)")
                
    except KeyboardInterrupt:
        print("\nStopping...")
        mixer.stop()

if __name__ == "__main__":
    main()
