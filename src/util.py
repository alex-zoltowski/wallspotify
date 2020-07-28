from winreg import OpenKey, CloseKey, QueryValueEx, SetValueEx, ConnectRegistry, \
    HKEY_CURRENT_USER, REG_SZ, KEY_ALL_ACCESS
from os import listdir
from os.path import abspath, join
from math import sqrt
from src.spotify import Spotify
from ssl import _create_unverified_context
from urllib.request import urlopen
from io import BytesIO
from PIL import Image
from time import sleep
from threading import Thread
import ctypes
import sys


class ChangeWallpaperThread(Thread):
    """
    this class defines the behavior for the thread that is created
    for the 'Toggle Wallpaper to Current Song Art' option
    """

    def __init__(self):
        Thread.__init__(self)
        self.running = False
        self.spotify = None
        self.path = None

    def stop(self):
        self.running = False
        print('Stopped - Current Song')

    def start(self):
        self.running = True
        Thread.start(self)
        print('Started - Current Song')

    def _smart_sleep(self, seconds):
        """this is used to prevent the thread from hanging after trying to stop it"""

        for _ in range(seconds):
            sleep(1)
            if not self.running:
                break

    def run(self):
        """
        runs until the user stops this action

        this thread handles checking for new songs
        """

        # used to save the previous image url
        previous_song = ''

        while self.running:
            # try to update wallpaper
            song_url = change_wallpaper(previous_song, self.spotify, self.path)

            # check for new song, save to previous_song
            if song_url:
                previous_song = song_url

            self._smart_sleep(5)


def resource_path(relative_path):
    """
    returns the absolute path to a file

    works for running with python and executable
    """

    try:
        base_path = sys._MEIPASS
    except:
        base_path = abspath('')

    return join(base_path, relative_path)


def handle_windows_reg_key():
    """
    Attempts to add this app to the list of apps that launch at startup

    checks for value in registry, creates one if it doesn't exist
    will update key with new location of .exe if it was moved
    """

    name = 'wallspotify'
    path = sys.executable
    registry = ConnectRegistry(None, HKEY_CURRENT_USER)
    key = OpenKey(registry, r'SOFTWARE\Microsoft\Windows\CurrentVersion\Run', 0, KEY_ALL_ACCESS)

    def add():
        SetValueEx(key, name, 0, REG_SZ, path)

    try:
        data = QueryValueEx(key, name)
        if data[0] != path:
            add()
    except WindowsError:
        add()

    CloseKey(key)


def cleanup_mei():
    """
    workaround for https://github.com/pyinstaller/pyinstaller/issues/2379
    """
    from shutil import rmtree

    mei_bundle = getattr(sys, "_MEIPASS", False)

    if mei_bundle:
        dir_mei, current_mei = mei_bundle.split("_MEI")
        for file in listdir(dir_mei):
            if file.startswith("_MEI") and not file.endswith(current_mei):
                try:
                    rmtree(join(dir_mei, file))
                except PermissionError:
                    pass


def choose_color_algo(colors):
    """
    This will attempt to find a non-white/gray/black, unique color from a selection of colors

    returns a tuple of RGB values (32, 34, 243)
    """

    fil_colors = [(freq, color) for freq, color in colors if (max(color) - min(color)) > 40]

    num_cands = 500
    cand_cols = sorted(fil_colors, key=lambda x: x[0], reverse=True)[:num_cands]

    if not cand_cols:
        return (0, 0, 0)

    max_col = cand_cols[0][1]
    max_dist = 0
    total_freq = sum([freq for freq, _ in cand_cols])

    # im = Image.new('RGB', (1000, 300), (0, 0, 0))

    j = 0
    for _, cand_col in cand_cols:

        dist = 0

        for freq, col in cand_cols:
            d = 0
            for i in range(3):
                d += (cand_col[i] - col[i]) ** 2
            dist += (freq / total_freq) * sqrt(d)

        dist = dist * (max(cand_col) - min(cand_col))

        if dist >= max_dist:
            max_col = cand_col
            max_dist = dist

        # im.paste(Image.new('RGB', (int(1000 / num_cands), 200), cand_col), (int(1000 / num_cands) * j, 0))
        j += 1

    # im.paste(Image.new('RGB', (1000, 100), max_col), (0, 200))
    # im.show()

    return max_col


def login(token_info):
    """creates the spotify object, logs user into their account with given token"""

    try:
        spotify = Spotify(auth=token_info['access_token'])
    except:
        # todo: add message box saying couldn't connect to spotify
        print('could not connect to Spotify with given token, exiting...')
        return None

    return spotify


def change_wallpaper(previous_song, spotify, path):
    """
    driver for all methods needed to download the new image and set as wallpaper

        returns url
                None on failure, AND when the song is the same as previous_song
    """

    # get the image url of the currently playing song
    url = get_current_song_image_url(spotify)
    if not url:
        return None

    # check if the same song is still playing
    if previous_song == url:
        return None

    # download the image from spotify
    img = download_image(url)
    if not img:
        return None

    # create the solid colored 1920x1080 background image
    bg_img = create_colored_background(img)
    if not bg_img:
        return None

    # create the full desktop image
    if not create_wallpaper_image(bg_img, img, path):
        return None

    # set the new image as the desktop wallpaper
    if not set_wallpaper_image(path):
        return None

    return url


def get_current_song_image_url(spotify):
    """
    get user's current song image url from spotify

    returns url
            None on failure
    """

    # call to spotify for current song info
    try:
        current_song = spotify.current_user_playing_track()
    except:
        print('failed current song request')
        return None

    # check if the data is there
    if current_song is None:
        print('no song info found, no song playing?')
        return None

    # get the url of the album art image
    try:
        url = current_song['item']['album']['images'][0]['url']
    except:
        print('could not find url in the spotify data')
        return None

    return url


def create_colored_background(img):
    """
    creates a 1920x1080 image with the most frequently used color in img.

    returns PIL Image
            None on failure
    """

    bg_col = choose_color_algo(img.getcolors(maxcolors=409601))

    # create the image using the chosen color
    try:
        bg_img = Image.new('RGB', (1920, 1080), bg_col)
    except:
        print('failed to create bg image')
        return None

    return bg_img


def create_wallpaper_image(bg_img, img, path):
    """
    combines the colored bg_img with the img downloaded from spotify then
    saves the image file

    returns True on success
            False on failure
    """

    # get image sizes
    img_w, img_h = img.size
    bg_w, bg_h = bg_img.size

    # create offset to paste img in the middle of bg_img
    offset = ((bg_w - img_w) // 2, (bg_h - img_h) // 2)
    bg_img.paste(img, offset)

    # save the image to the unique filename
    try:
        bg_img.save(path)
    except:
        print('could not save finished image')
        return False

    return True


def download_image(url):
    """
    downloads an image given a url

    returns PIL Image
            None on failure
    """

    # download the image data
    context = _create_unverified_context()
    try:
        with urlopen(url, context=context) as response:
            data = response.read()
    except:
        print('failed to download image')
        return None

    # create PIL image from image data
    try:
        img = Image.open(BytesIO(data)).convert('RGB')
    except:
        print('could not create PIL image from downloaded data')
        return None

    return img


def set_wallpaper_image(path):
    """
    sets the desktop wallpaper

    returns True on success
            False on failure
    """

    try:
        ctypes.windll.user32.SystemParametersInfoW(20, 0, path, 0)
    except:
        print('could not set bg image')
        return False

    return True
