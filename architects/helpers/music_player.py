import sys

from PySide6.QtCore import QCoreApplication, QUrl
from PySide6.QtMultimedia import QAudioOutput, QMediaDevices, QMediaPlayer

def _choose_output(device_pref=1):
    devices = QMediaDevices.audioOutputs()
    default_device = QMediaDevices.defaultAudioOutput()
    print(f"Found {len(devices)} audio outputs")
    for idx, device in enumerate(devices):
        print(f"  [{idx}] {device.description()}")
    if default_device:
        print(f"Default audio output: {default_device.description()}")
    else:
        print("No default audio output")

    if device_pref is not None:
        # Accept either index or substring match for convenience.
        if isinstance(device_pref, int):
            if 0 <= device_pref < len(devices):
                print(f"Selecting device index {device_pref}")
                return QAudioOutput(devices[device_pref])
            print(f"Device index {device_pref} out of range, falling back to default")
        else:
            pref = str(device_pref).lower()
            for device in devices:
                if pref in device.description().lower():
                    print(f"Selecting device by name match: {device.description()}")
                    return QAudioOutput(device)
            print(f"No device matched '{device_pref}', falling back to default")

    if default_device:
        return QAudioOutput(default_device)
    return QAudioOutput()


def play_music(path, device_pref=None):
    audio = _choose_output(device_pref)
    player = QMediaPlayer()
    print(f"Using output: {audio.device().description()}")
    player.setAudioOutput(audio)
    player.setSource(QUrl.fromLocalFile(path))
    audio.setVolume(0.8)

    def on_error(err, error_str):
        if err != QMediaPlayer.NoError:
            print(f"Player error {err}: {error_str}")

    def on_state_change(state):
        if state == QMediaPlayer.PlayingState:
            print("State: Playing")
        elif state == QMediaPlayer.PausedState:
            print("State: Paused")
        elif state == QMediaPlayer.StoppedState:
            print("State: Stopped")

    player.errorOccurred.connect(on_error)
    player.playbackStateChanged.connect(on_state_change)

    player.play()

    # Prevent garbage collection
    player._keepalive = True
    audio._keepalive = True

    return player

if __name__ == "__main__":
    app = QCoreApplication(sys.argv)

    TEST_MUSIC = "/home/mintmainog/workspace/vs_code_workspace/dj-blue-ai/mood_readers/deep_purple_smoke_on_the_water.wav"
    # Optional: pass a device index or substring (e.g., "analog") as the second CLI arg.
    chosen_device = None
    if len(sys.argv) > 2:
        try:
            chosen_device = int(sys.argv[2])
        except ValueError:
            chosen_device = sys.argv[2]
    player = play_music(TEST_MUSIC if len(sys.argv) <= 1 else sys.argv[1], chosen_device)

    def stop_app_on_end(status):
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            app.quit()
        elif status == QMediaPlayer.MediaStatus.InvalidMedia:
            print("Media invalid")
            app.quit()
        elif status == QMediaPlayer.MediaStatus.NoMedia:
            print("No media")

    player.mediaStatusChanged.connect(stop_app_on_end)
    sys.exit(app.exec())
