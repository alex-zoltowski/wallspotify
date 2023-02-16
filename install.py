import subprocess
import sys


_all_ = [
    "PyQt5>=5.12.2",
    "Pillow>=7.2.0",
    "requests>=2.24.0",
    "pyinstaller>=3.6",
    "lyricsgenius>=3.0.1"
]

windows = ["winotify>=1.1.0"]

darwin = ["appscript>=1.1.0"]

def install(packages):
    for package in packages:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])

if __name__ == '__main__':
    if sys.platform == 'win32':
        install(windows)
    elif sys.platform == 'darwin':
        install(darwin) 
    else:
        print("wallspotify does not support this operation system")
        exit()

    install(_all_)
