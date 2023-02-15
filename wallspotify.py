from os.path import expanduser, exists, join
from os import makedirs, listdir
from src.application import Application
from src.functions import cleanup_mei, create_windows_reg_key, set_wallpaper_image
import sys


def main():
    is_windows = sys.platform == 'win32'

    # Path to hidden wallspotify folder within the users home folder
    folder_path = join(expanduser('~'), '.wallspotify')

    # Check if program is running as an executable
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        # Delete any previous temp folders created from the executable
        cleanup_mei()

        if is_windows:
            # Add executable to list of start up apps
            create_windows_reg_key()

    # Check if wallspotify folder already exists
    if exists(folder_path):
        for item in listdir(folder_path):
            if item.endswith('.jpeg'):
                # If wallpaper image exists from last wallspotify session, set it as background image
                set_wallpaper_image(join(folder_path, item))
                break
    else:
        # Create the hidden wallspotify folder
        makedirs(folder_path)

    # Create and start application
    app = Application(folder_path, is_windows)
    app.exec_()


if __name__ == '__main__':
    main()
