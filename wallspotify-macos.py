"""
<placeholder>
"""

from platform import system
from time import sleep
from threading import Thread
from os.path import abspath, join, expanduser, dirname, exists
from os import listdir, remove, makedirs
from ssl import _create_unverified_context
from datetime import datetime
from urllib.request import urlopen
from webbrowser import open as open_webbrowser
from io import BytesIO
from re import match, compile, IGNORECASE
from PIL import Image
from PyQt5.QtCore import QEvent
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QWidget, QMenu, QPushButton, QAction, \
    QSystemTrayIcon, QVBoxLayout, QLabel, QLineEdit, QMainWindow
from spotipy import Spotify, oauth2
from math import sqrt
import ctypes
import winreg
import sys


class Application(QApplication):
    """this class configures our application"""

    def __init__(self):
        super(Application, self).__init__([])
        self.setQuitOnLastWindowClosed(False)

        self.wallpaper_thread = None
        self.spotify = None

        # Create the menu
        self.menu = Menu()
        self.menu.login_info_action.triggered.connect(self.token_prompt)

        # Create the tray
        self.tray = QSystemTrayIcon()
        self.tray.setIcon(QIcon(resource_path('icon.png')))
        self.tray.setVisible(True)
        self.tray.setContextMenu(self.menu)

        # Create confirm account frame
        self.confirm_account_window = ConfirmAccountWindow()

        # defines the permissions that are used to get spotify user data
        scope = 'user-read-currently-playing'

        # app info
        client_id = '7a1a08fc6f844668b7f09bfacce63241'
        client_secret = '32214e01a06c4d6d85ec77bdb9d96c0a'
        redirect_uri = 'https://www.google.com'

        # Create ouath object to handle token data
        self.sp_oauth = oauth2.SpotifyOAuth(client_id,
                                            client_secret,
                                            redirect_uri,
                                            scope=scope,
                                            cache_path=f'{FOLDER}\spotifycache')

    def handle_token(self):
        """try to get a token from cache - if it doesn't exist, prompt user for token"""

        cached_token_info = self.sp_oauth.get_cached_token()
        if cached_token_info:
            print('token found, attempting login')
            self.login(cached_token_info)
        else:
            print('token not found, opening token prompt')
            self.token_prompt()

    def login(self, token_info):
        """creates the spotify object, logs user into their account with given token"""

        try:
            self.spotify = Spotify(auth=token_info['access_token'])
        except:
            print('could not connect to spotify with given token, exiting...')
            # todo: add message box saying couldn't connect to spotify
            self.exit()

        # get spotify username and show it in the menu
        try:
            current_user_info = self.spotify.current_user()
            text = f'{current_user_info["display_name"]} - Logged into Spotify'
        except:
            text = 'Logged into Spotify'
            print('could not get user info')

        self.menu.login_info_action.setText(text)
        self.menu.current_song_action.setEnabled(True)
        self.menu.login_info_action.setEnabled(False)

        # todo: message box saying successful login

    def token_prompt(self):
        """prompts user to input the callback url"""

        if not self.confirm_account_window.isVisible():
            self.confirm_account_window.show()
            auth_url = self.sp_oauth.get_authorize_url()
            try:
                open_webbrowser(auth_url)
            except:
                # todo: add a message box to give the user the auth url
                print('could not open token prompt')

    def event(self, event):
        """Ignore command + q close app keyboard shortcut event in mac"""

        if event.type() == QEvent.Close and not event.spontaneous():
                event.ignore()
                quit_application()
                return False

        return True


class ConfirmAccountWindow(QMainWindow):
    """this class sets up the window that displays the confirm account widget"""

    def __init__(self):
        super(ConfirmAccountWindow, self).__init__()
        self.form_widget = ConfirmAccountWidget(self)
        self.setCentralWidget(self.form_widget)


class ConfirmAccountWidget(QWidget):
    """this class sets up the design for the confirm account window"""

    def __init__(self, parent):
        super(ConfirmAccountWidget, self).__init__(parent)
        self.layout = QVBoxLayout(self)
        label_text = 'Paste the link from the web browser after logging into spotify\n(should be a google url):'
        self.layout.addWidget(QLabel(label_text))
        self.text_field = QLineEdit()
        self.layout.addWidget(self.text_field)
        self.button = QPushButton('Confirm Account')
        self.layout.addWidget(self.button)
        self.button.clicked.connect(self.on_button_click)
        self.setLayout(self.layout)

    def on_button_click(self):
        """defines behavior for button press"""

        # create regex for a valid url
        regex = compile(
            r'^(?:http|ftp)s?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?:/?|[/?]\S+)$', IGNORECASE)

        # get the contents of the text field
        text = self.text_field.text()

        # check for valid url
        if match(regex, text):
            code = APPLICATION.sp_oauth.parse_response_code(text)

            if not code:
                print('could not parse response code')
                # todo: not a valid url
                return
        else:
            print('invalid url')
            # todo: not a valid url, 'make sure it starts with https://'
            return

        # hide the window
        APPLICATION.confirm_account_window.hide()

        # get access token from Spotify
        try:
            token_info = APPLICATION.sp_oauth.get_access_token(code)
        except:
            # todo: show message box saying it failed
            print('could not get access token from spotify')
            return

        # if token info exists, login
        if token_info:
            APPLICATION.login(token_info)
        else:
            # todo: show message box saying it failed
            pass

        # todo: show user the successful login, guide them to the task bar


class Menu(QMenu):
    """this class defines the gui menu used by the tray class"""

    def __init__(self):
        super(Menu, self).__init__()
        self.current_song_action = QAction('Toggle - Wallpaper to Current Song Art')
        self.login_info_action = QAction('Login to Spotify')
        self.quit_action = QAction('Quit')

        self.setup_current_song_action()
        self.addSeparator()
        self.setup_login_info_action()
        self.setup_quit_action()

    def setup_current_song_action(self):
        """sets up the Toggle - Current Song option"""

        self.current_song_action.setCheckable(True)
        self.current_song_action.checked = False
        self.current_song_action.triggered.connect(wallpaper_to_current_song)
        self.current_song_action.setEnabled(False)
        self.addAction(self.current_song_action)

    def setup_login_info_action(self):
        """sets up the Login option"""

        self.addAction(self.login_info_action)

    def setup_quit_action(self):
        """sets up the quit option"""

        self.quit_action.triggered.connect(quit_application)
        self.addAction(self.quit_action)


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

            # clean up any jpeg's we created
            #delete_jpegs()


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
    img_file_name = create_wallpaper_image(bg_img, img)
    if not img_file_name:
        return None

    # set the new image as the desktop wallpaper
    if not set_desktop_image(img_file_name):
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

    returns image file name
            None on failure
    """

    # get image sizes
    img_w, img_h = img.size
    bg_w, bg_h = bg_img.size

    # create offset to paste img in the middle of bg_img
    offset = ((bg_w - img_w) // 2, (bg_h - img_h) // 2)
    bg_img.paste(img, offset)

    # get unique filename for the desktop wallpaper image file
    img_file_name = 'background.jpeg'#datetime.now().strftime('%Y%m%d%H%M%S') + '.jpeg'

    # save the image to the unique filename
    try:
        bg_img.save(f'{FOLDER}\{img_file_name}')
    except:
        print('could not save finished image')
        return None

    return 1


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
        img = Image.open(BytesIO(data))
    except:
        print('could not create PIL image from downloaded data')
        return None

    return img


def set_desktop_image(filename):
    """
    sets the desktop wallpaper

    returns True on success
            False on failure
    """

    try:
        # get path to the file
        path = f'{FOLDER}\\background.jpeg'

        # set background image based on the user's os
        if IS_WINDOWS:
            ctypes.windll.user32.SystemParametersInfoW(20, 0, path, 0)
        else:
            app('Finder').desktop_picture.set(mactypes.File(path))
    except:
        print('could not set bg image')
        return False

    return True


def get_current_song_image_url():
    """
    get user's current song image url from spotify

    returns url
            None on failure
    """

    # call to spotify for current song info
    try:
        current_song = APPLICATION.spotify.current_user_playing_track()
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


def resource_path(relative_path):
    """returns the absolute path to a file"""

    try:
        base_path = sys._MEIPASS
    except:
        base_path = abspath('.')

    return join(base_path, relative_path)


def wallpaper_to_current_song():
    """this toggles the wallpaper to current song option"""

    # check if the current song option was already selected
    if APPLICATION.menu.current_song_action.checked:
        # stop the current song thread
        APPLICATION.menu.current_song_action.checked = False
        APPLICATION.wallpaper_thread.stop()
    else:
        # start a new current song thread
        APPLICATION.menu.current_song_action.checked = True
        APPLICATION.wallpaper_thread = ChangeWallpaperThread()
        APPLICATION.wallpaper_thread.start()


def delete_jpegs():
    """deletes any '.jpeg' files that were created"""

    try:
        path = sys._MEIPASS
    except:
        path = '.'

    for item in listdir(path):
        if item.endswith('.jpeg'):
            remove(join(path, item))


def quit_application():
    """stops any threads then quits the application"""

    try:
        APPLICATION.wallpaper_thread.stop()
    except:
        pass

    APPLICATION.quit()

def handle_windows_startup():
    """checks for value in registry, creates one if it doesn't exist"""

    name = 'wallspotify'
    path = sys.executable
    registry = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
    key = winreg.OpenKey(registry, r'SOFTWARE\Microsoft\Windows\CurrentVersion\Run', 0, winreg.KEY_ALL_ACCESS)

    def add():
        winreg.SetValueEx(key, name, 0, winreg.REG_SZ, path)

    try:
        data = winreg.QueryValueEx(key, name)
        if data[0] != path:
            add()
    except WindowsError:
        add()

    winreg.CloseKey(key)


if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        handle_windows_startup()

FOLDER = join(expanduser('~'), '.wallspotify')
IMG_PATH = join(FOLDER, "background.jpeg")

if not exists(FOLDER):
    makedirs(FOLDER)
else:
    if exists(IMG_PATH):
        set_desktop_image(IMG_PATH)

# create our application
APPLICATION = Application()

# get user token
APPLICATION.handle_token()

# start the gui application
APPLICATION.exec_()

print("hi")


if __name__ == '__main__':
    main()
