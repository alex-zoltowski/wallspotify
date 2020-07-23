from PyQt5.QtWidgets import QMenu, QAction


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
        self.current_song_action.setEnabled(False)
        self.addAction(self.current_song_action)

    def setup_login_info_action(self):
        """sets up the Login option"""

        self.addAction(self.login_info_action)

    def setup_quit_action(self):
        """sets up the quit option"""

        self.addAction(self.quit_action)
