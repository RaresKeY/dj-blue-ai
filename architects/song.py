from pathlib import Path
from architects.helpers.managed_mem import ManagedMem

class Song():
    def __init__(self, song_filepath):
        # Required
        path_obj = Path(song_filepath)
        self.filepath: Path = path_obj
        self.mood_tags: list[str] = None
        self.camelot_tags: list[str] = None
        self.tempo: int = None

        # Managed Mem Singleton
        self.mem_man = ManagedMem()

        # Optional
        self.duration: float = None
        self.bitrate: int = None

        # Load data
        data = self._read_data(path_obj)

        if not data:
            self._write_data(path_obj)

    def _read_data(self, path_obj):
        """ read filepath key value from managed mem """
        key = self._normalize_key(path_obj)
        return self.mem_man.gettr(key)
    
    def _write_data(self, path_obj):
        """ generate and write self in managed mem, key is filepath """
        key = self._normalize_key(path_obj)

        # Required
        self._get_tags()
        self._get_camelot()
        self._get_tempo()

        # Optional
        self._get_duration()

        self.mem_man.settr(key, self)

    def _get_tags(self):
        # read music librarians tag list (use managed mem?)
        pass

    def _get_camelot(self):
        # use mood readers script to determine camelot
        pass

    def _get_tempo(self):
        # use mood readers script to determine tempo
        pass

    def _get_duration(self):
        # use pyaudio to get duration (could be useful for queue operations)
        pass

    @staticmethod
    def _normalize_key(song_filepath):
        if isinstance(song_filepath, Path):
            return str(song_filepath)
        return str(song_filepath)
