from time import sleep
from threading import Thread
from os.path import abspath, join, expanduser, exists
from os import makedirs, listdir
from ssl import _create_unverified_context
from urllib.request import urlopen
from webbrowser import open as open_webbrowser
from io import BytesIO
from re import match, compile, IGNORECASE
from PIL import Image
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QSystemTrayIcon
from src.spotify import Spotify
from src.oauth2 import SpotifyOAuth, SpotifyOauthError
from math import sqrt
from winreg import OpenKey, CloseKey, QueryValueEx, SetValueEx, ConnectRegistry, \
    HKEY_CURRENT_USER, REG_SZ, KEY_ALL_ACCESS
from src.menu import Menu
from src.confirm_account_window import ConfirmAccountWindow
import ctypes
import sys
from src import spotify_config

FOLDER = join(expanduser('~'), '.wallspotify')
IMG_PATH = join(FOLDER, 'background.jpeg')

# Create ouath object to handle cached token data
SCOPE = 'user-read-currently-playing'
SP_OAUTH = SpotifyOAuth(spotify_config.client_id,
                        spotify_config.client_secret,
                        spotify_config.redirect_uri,
                        scope=SCOPE,
                        cache_path=join(FOLDER, 'spotifycache'))


class Application(QApplication):

    def __init__(self):
        super(Application, self).__init__([])
        self.setQuitOnLastWindowClosed(False)

        self.wallpaper_thread = None

        # Create the menu, connect class functions to the app's buttons
        self.menu = Menu()
        self.menu.login_info_action.triggered.connect(self._on_login_button)
        self.menu.toggle_wallpaper_action.triggered.connect(self._on_toggle_wallpaper_button)
        self.menu.quit_action.triggered.connect(self._on_quit_button)

        # Create the tray and make it visible
        self.tray = QSystemTrayIcon()
        self.tray.setIcon(QIcon(resource_path(join('assets', 'icon.png'))))
        self.tray.setVisible(True)
        self.tray.setContextMenu(self.menu)

        # Create confirm account frame
        self.confirm_account_window = ConfirmAccountWindow()
        self.confirm_account_window.form_widget.button.clicked.connect(self._on_confirm_account_button)

        # Attempt login with cache
        self._attempt_login()

    def _attempt_login(self, code=None):
        """attempts to get token from cache if a code is not supplied"""

        if code:
            # Get access token from Spotify
            try:
                token_info = SP_OAUTH.get_access_token(code)
            except SpotifyOauthError:
                # todo: show message box saying it failed
                print('could not get access token from Spotify')
                return
        else:
            # Get token from cache
            token_info = SP_OAUTH.get_cached_token()
            if not token_info:
                return

        # Login with token
        login_response = login(token_info)

        if login_response:
            self._update_login_ui(login_response)
            self.confirm_account_window.hide()
        else:
            print('login with token failed')
            # todo: show user login failed

    def _update_login_ui(self, text):
        """changes tray UI to reflect a successful login"""

        self.menu.login_info_action.setText(text)
        self.menu.toggle_wallpaper_action.setEnabled(True)
        self.menu.login_info_action.setEnabled(False)

    def _on_confirm_account_button(self):
        """defines behavior for button press"""

        # create regex for a valid url
        regex = compile(
            r'^(?:http|ftp)s?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?:/?|[/?]\S+)$', IGNORECASE)

        # get the contents of the text field
        text = self.confirm_account_window.form_widget.text_field.text()

        # check if text is a valid url
        if match(regex, text):
            code = SP_OAUTH.parse_response_code(text)

            if not code:
                print('could not parse response code')
                # todo: not a valid url
                return
        else:
            print('invalid url')
            # todo: not a valid url, 'make sure it starts with https://'
            return

        # Clear text field
        self.confirm_account_window.form_widget.text_field.setText("")

        # Attempt login using code
        self._attempt_login(code)

    def _on_login_button(self):
        """tries to open users web browser to prompt Spotify login, also shows window for callback url"""

        if not self.confirm_account_window.isVisible():
            self.confirm_account_window.show()
            auth_url = SP_OAUTH.get_authorize_url()
            try:
                open_webbrowser(auth_url)
            except:
                # todo: show a prompt to give the user the auth url
                print('could not open web browser')

    def _on_toggle_wallpaper_button(self):
        """this toggles the wallpaper to current song option"""

        # check if the current song option was already selected
        if self.menu.toggle_wallpaper_action.checked:
            # stop the current song thread
            self.menu.toggle_wallpaper_action.checked = False
            self.wallpaper_thread.stop()
        else:
            # start a new current song thread
            self.menu.toggle_wallpaper_action.checked = True
            self.wallpaper_thread = ChangeWallpaperThread()
            self.wallpaper_thread.start()

    def _on_quit_button(self):
        """stops any threads then quits the application"""

        try:
            self.wallpaper_thread.stop()
        except:
            pass

        self.quit()


class ChangeWallpaperThread(Thread):
    """
    this class defines the behavior for the thread that is created
    for the 'Toggle Wallpaper to Current Song Art' option
    """

    def __init__(self):
        Thread.__init__(self)
        self.running = False

    def stop(self):
        """stops thread"""

        self.running = False
        print('Stopped - Current Song')

    def start(self):
        """starts thread"""

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

        this thread handles checking for new songs - if so, it updates the
        wallpaper to album art, sleeps, then deletes any jpeg's created.
        """

        # used to save the previous image url
        previous_song = ''

        while self.running:
            # try to update wallpaper
            song_url = change_wallpaper(previous_song)

            # check for new song, save to previous_song
            if song_url:
                previous_song = song_url

            self._smart_sleep(5)


def login(token_info):
    """creates the spotify object, logs user into their account with given token"""

    try:
        global spot
        spot = Spotify(auth=token_info['access_token'])
    except:
        print('could not connect to spotify with given token, exiting...')
        # todo: add message box saying couldn't connect to spotify

    try:
        current_user_info = spot.me()
        text = f'{current_user_info["display_name"]} - Logged into Spotify'
        return text
    except:
        print('could not get user info')

    return None


def change_wallpaper(previous_song):
    """
    driver for all methods needed to download the new image and set as wallpaper

        returns url
                None on failure, AND when the song is the same as previous_song
    """

    # get the image url of the currently playing song
    url = get_current_song_image_url()
    if not url:
        return None

    # check if the same song is still playing
    if previous_song == url:
        return None

    # download the image from spotify
    img = download_img(url)
    if not img:
        return None

    # create the solid colored 1920x1080 background image
    bg_img = create_colored_background(img)
    if not bg_img:
        return None

    # create the full desktop image
    if not create_wallpaper_image(bg_img, img):
        return None

    # set the new image as the desktop wallpaper
    if not set_desktop_image():
        return None

    return url


def get_current_song_image_url():
    """
    get user's current song image url from spotify

    returns url
            None on failure
    """

    # call to spotify for current song info
    try:
        current_song = spot.current_user_playing_track()
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


def create_wallpaper_image(bg_img, img):
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
        bg_img.save(IMG_PATH)
    except:
        print('could not save finished image')
        return False

    return True


def download_img(url):
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


def set_desktop_image():
    """
    sets the desktop wallpaper

    returns True on success
            False on failure
    """

    try:
        ctypes.windll.user32.SystemParametersInfoW(20, 0, IMG_PATH, 0)
    except:
        print('could not set bg image')
        return False

    return True


def resource_path(relative_path):
    """returns the absolute path to a file"""

    try:
        base_path = sys._MEIPASS
    except:
        base_path = abspath('')

    return join(base_path, relative_path)


def handle_windows_startup():
    """checks for value in registry, creates one if it doesn't exist"""

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
    Rudimentary workaround for https://github.com/pyinstaller/pyinstaller/issues/2379
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


def main():
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        handle_windows_startup()
        cleanup_mei()

    if exists(FOLDER):
        if exists(IMG_PATH):
            set_desktop_image()
    else:
        makedirs(FOLDER)

    application = Application()
    application.exec_()


if __name__ == '__main__':
    main()
