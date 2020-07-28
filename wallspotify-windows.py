from os.path import expanduser, exists
from os import makedirs
from webbrowser import open as open_webbrowser
from re import match, compile, IGNORECASE
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QSystemTrayIcon
from src.oauth2 import SpotifyOAuth, SpotifyOauthError
from src.menu import Menu
from src.confirm_account_window import ConfirmAccountWindow
from src import spotify_config
from src.util import *
import sys


FOLDER = join(expanduser('~'), '.wallspotify')
IMG_PATH = join(FOLDER, 'background.jpeg')


class Application(QApplication):

    def __init__(self):
        super(Application, self).__init__([])
        self.setQuitOnLastWindowClosed(False)

        # Create ouath object to handle cached token data
        self.sp_oauth = SpotifyOAuth(spotify_config.client_id,
                                     spotify_config.client_secret,
                                     spotify_config.redirect_uri,
                                     scope='user-read-currently-playing',
                                     cache_path=join(FOLDER, 'spotifycache'))

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
                token_info = self.sp_oauth.get_access_token(code)
            except SpotifyOauthError:
                # todo: show message box saying it failed
                print('could not get access token from Spotify')
                return
        else:
            # Get token from cache
            token_info = self.sp_oauth.get_cached_token()
            if not token_info:
                return

        # Login with token
        self.spotify = login(token_info)

        if self.spotify:
            self._update_login_ui()
            self.confirm_account_window.hide()
        else:
            print('login with token failed')
            # todo: show user login failed

    def _update_login_ui(self):
        """changes tray UI to reflect a successful login"""
        try:
            current_user_info = self.spotify.me()
        except Exception as e:
            print(e)
            return

        text = f'{current_user_info["display_name"]} - Logged into Spotify'

        self.menu.login_info_action.setText(text)
        self.menu.toggle_wallpaper_action.setEnabled(True)
        self.menu.login_info_action.setEnabled(False)

    def _on_confirm_account_button(self):
        """parse Spotify callback url for response code, then try to login"""

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
            code = self.sp_oauth.parse_response_code(text)

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
            auth_url = self.sp_oauth.get_authorize_url()
            try:
                open_webbrowser(auth_url)
            except Exception as e:
                # todo: show a prompt to give the user the auth url
                print(e)

    def _on_toggle_wallpaper_button(self):
        """starts and stops wallpaper thread from users input"""

        # check if the toggle wallpaper option was already selected
        if self.menu.toggle_wallpaper_action.checked:
            # stop the current song thread
            self.menu.toggle_wallpaper_action.checked = False
            self.wallpaper_thread.stop()
        else:
            # start a new thread for changing wallpaper
            self.menu.toggle_wallpaper_action.checked = True
            self._start_new_thread()

    def _on_quit_button(self):
        """stops any threads then quits the application"""

        try:
            self.wallpaper_thread.stop()
        except:
            pass

        self.quit()

    def _start_new_thread(self):
        """creates new thread object and starts it"""

        self.wallpaper_thread = ChangeWallpaperThread()
        self.wallpaper_thread.spotify = self.spotify
        self.wallpaper_thread.path = IMG_PATH
        self.wallpaper_thread.start()


def main():

    # Check if it's running as an executable
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        handle_windows_reg_key()
        cleanup_mei()

    if exists(FOLDER):
        if exists(IMG_PATH):
            # Set wallpaper image if it exists
            set_wallpaper_image(IMG_PATH)
    else:
        # Create hidden folder in home directory to store cache and background image
        makedirs(FOLDER)

    # Create and start app
    app = Application()
    app.exec_()


if __name__ == '__main__':
    main()
