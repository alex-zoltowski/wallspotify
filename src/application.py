from os import system
from os.path import join
from webbrowser import open as open_webbrowser
from re import match, compile, IGNORECASE
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QSystemTrayIcon
from src.oauth2 import SpotifyOAuth, SpotifyOauthError
from src.menu import Menu
from src.confirm_account_window import ConfirmAccountWindow
from src.spotify_config import client_id, client_secret, redirect_uri
from src.functions import resource_path, login
from src.change_wallpaper_thread import ChangeWallpaperThread


class Application(QApplication):

    def __init__(self, folder_path, is_windows):
        super(Application, self).__init__([])
        self.folder_path = folder_path
        self.is_windows = is_windows

        if self.is_windows:
            from win10toast import ToastNotifier
            self.notifier = ToastNotifier()

        self.setQuitOnLastWindowClosed(False)

        # Create ouath object to handle cached token data
        self.sp_oauth = SpotifyOAuth(client_id,
                                     client_secret,
                                     redirect_uri,
                                     scope='user-read-currently-playing',
                                     cache_path=join(self.folder_path, 'spotifycache'))

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
                return
        else:
            # Get token from cache
            token_info = self.sp_oauth.get_cached_token()
            if not token_info:
                if self.is_windows:
                    text = 'Find the WallSpotify icon in your tray to log into your Spotify account.'
                else:
                    text = 'Click the WallSpotify icon to log into your Spotify account.'
                self._show_notification('Not Logged In', text)
                return

        # Login with token
        self.spotify = login(token_info)

        if self.spotify:
            self._update_login_ui()
            self._show_notification('Login Success', 'You can now use WallSpotify.')
        else:
            self._show_notification('Login Failed',
                              'Something went wrong, try logging in again.')

    def _update_login_ui(self):
        """changes tray UI to reflect a successful login"""

        # Call to Spotify for user account info
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

        is_valid = True
        # check if text is a valid url
        if match(regex, text):
            code = self.sp_oauth.parse_response_code(text)

            if not code:
                is_valid = False
        else:
            is_valid = False

        self.confirm_account_window.hide()
        self.confirm_account_window.form_widget.text_field.setText('')

        if is_valid:
            # Attempt login using code
            self._attempt_login(code)
        else:
            self._notify_bad_link()

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

        self.wallpaper_thread = ChangeWallpaperThread(self.spotify, self.folder_path)
        self.wallpaper_thread.start()


    def _show_notification(self, title, body):
        """shows a notification based on the OS"""

        if self.is_windows:
            self.notifier.show_toast(title,
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