from os.path import expanduser, exists
from os import makedirs, system
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


IS_WINDOWS = sys.platform == 'win32'
if IS_WINDOWS:
    from win10toast import ToastNotifier
    NOTIFIER = ToastNotifier()

FOLDER_PATH = join(expanduser('~'), '.wallspotify')


class Application(QApplication):

    def __init__(self):
        super(Application, self).__init__([])
        self.setQuitOnLastWindowClosed(False)

        # Create ouath object to handle cached token data
        self.sp_oauth = SpotifyOAuth(spotify_config.client_id,
                                     spotify_config.client_secret,
                                     spotify_config.redirect_uri,
                                     scope='user-read-currently-playing',
                                     cache_path=join(FOLDER_PATH, 'spotifycache'))

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
                self._notify_bad_link()
                print('could not get access token from Spotify')
                return
        else:
            # Get token from cache
            token_info = self.sp_oauth.get_cached_token()
            if not token_info:
                self._show_notification('Not Logged In',
                                        'Right-Click the WallSpotify icon to login to your Spotify account.')
                return

        # Login with token
        self.spotify = login(token_info)

        if self.spotify:
            self._update_login_ui()
            self._show_notification('Login Success', 'You can now use WallSpotify.')
        else:
            self._show_notification('Login Failed',
                                    'Something went wrong, try logging in again.')
            print('login with token failed')

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
                self._notify_bad_link()
                print('could not parse response code')
                return
        else:
            self._notify_bad_link()
            print('invalid url')
            return

        # Close text field
        self.confirm_account_window.hide()

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
        """stops thread then quits the application"""

        try:
            self.wallpaper_thread.stop()
        except AttributeError:
            pass

        self.quit()

    def _start_new_thread(self):
        """creates new thread object and starts it"""

        self.wallpaper_thread = ChangeWallpaperThread()
        self.wallpaper_thread.spotify = self.spotify
        self.wallpaper_thread.path = FOLDER_PATH
        self.wallpaper_thread.start()

    def _show_notification(self, title, body):
        if IS_WINDOWS:
            NOTIFIER.show_toast(title,
                                body,
                                icon_path=resource_path(join('assets', 'icon.ico')),
                                duration=4,
                                threaded=True)
        else:
            system("""
                          osascript -e 'display notification "{}" with title "{}"'
                          """.format(body, title))

    def _notify_bad_link(self):
        self._show_notification('Login Failed',
                                'Something is wrong with the link, be sure to copy and paste the entire link.')


def main():
    # Check if it's running as an executable
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        cleanup_mei()

        if IS_WINDOWS:
            handle_windows_reg_key()

    if exists(FOLDER_PATH):
        for item in listdir(FOLDER_PATH):
            if item.endswith('.jpeg'):
                # Set wallpaper image if it exists
                set_wallpaper_image(join(FOLDER_PATH, item))
                break
    else:
        # Create hidden folder in home directory to store cache and background image
        makedirs(FOLDER_PATH)

    # Create and start application
    app = Application()
    app.exec_()


if __name__ == '__main__':
    main()
