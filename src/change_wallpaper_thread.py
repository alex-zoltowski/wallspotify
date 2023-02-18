from time import sleep
from threading import Thread
from datetime import datetime
from os.path import join
from src.functions import change_wallpaper, delete_old_jpegs


class ChangeWallpaperThread(Thread):
    """
    this class defines the behavior for the thread that is created
    for the 'Toggle Wallpaper to Current Song Art' option
    """

    def __init__(self, spotify, path):
        Thread.__init__(self)
        self.running = False
        self.spotify = spotify
        self.path = path

    def stop(self):
        self.running = False

    def start(self):
        self.running = True
        Thread.start(self)

    def _smart_sleep(self, seconds):
        """this is used to prevent the thread from hanging after trying to stop it"""

        for _ in range(seconds):
            sleep(1)
            if not self.running:
                break

    def run(self):
        """when a thread is created it runs this function"""

        # used to save the previous image url
        prev_song_data = None

        while self.running:
            # get unique filename
            file_name = datetime.now().strftime('%Y%m%d%H%M%S') + '.jpeg'
            file_path = join(self.path, file_name)

            # try to update wallpaper
            current_song_data = change_wallpaper(prev_song_data, self.spotify, file_path)

            # check for new song, save to previous_song
            if current_song_data:
                prev_song_data = current_song_data
                delete_old_jpegs(self.path, file_name)

            self._smart_sleep(5)