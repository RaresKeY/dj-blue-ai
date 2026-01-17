import miniaudio
import os
import numpy as np

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

    def start(self):
        """Starts or resumes playback."""
        if self._running and self._paused:
                self.resume()
                return

        self.stop() # Ensure clean state

        if not os.path.exists(self.file_path):
            print(f"MiniaudioPlayer: File not found {self.file_path}")
            return

        try:
            # stream_file yields PCM chunks.
            # miniaudio detects format from file extension/header.
            raw_stream = miniaudio.stream_file(self.file_path)
            
            # Wrap stream to apply volume
            self._stream = self._volume_generator(raw_stream)
            
            # Prime the generator so it can accept send()
            next(self._stream)
            
            self._device = miniaudio.PlaybackDevice()
            self._device.start(self._stream)
            self._running = True
            self._paused = False
            print(f"MiniaudioPlayer: Playing {self.file_path} at volume {self._volume}")
        except Exception as e:
            print(f"MiniaudioPlayer Error: {e}")
            self._running = False

    def _volume_generator(self, stream):
        """Applies current volume to the PCM stream chunks."""
        # Prime the generator: yield empty bytes to allow the first send() to work
        yield b""
        
        for chunk in stream:
            if self._volume == 1.0:
                yield chunk
                continue
            
            # miniaudio.stream_file typically yields 16-bit PCM (int16)
            samples = np.frombuffer(chunk, dtype=np.int16)
            scaled = (samples * self._volume).astype(np.int16)
            yield scaled.tobytes()

    def set_volume(self, volume):
        """Sets the volume (0.0 to 1.0)."""
        self._volume = max(0.0, min(1.0, float(volume)))
        # Note: If already playing, the generator will pick up the new value 
        # on the next chunk because it accesses self._volume in each iteration.

        print(f"Volume: {self._volume}")

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

    def close(self):
        """Cleanup."""
        self.stop()
    
    @property
    def paused(self):
        return self._paused

    def is_playing(self):
        return self._running and not self._paused
