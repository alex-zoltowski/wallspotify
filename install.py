import subprocess
import sys

_all_ = [
    "PyQt5>=5.12.2",
    "Pillow>=7.2.0",
    "requests>=2.24.0",
    "pyinstaller>=3.6",
]

windows = ["win10toast>=0.9"]

linux = []

darwin = ["appscript>=1.1.0"]


def install(packages):
    for package in packages:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])


if __name__ == '__main__':

    from sys import platform

    install(_all_)
    if platform == 'win32':
        install(windows)
    if platform.startswith('linux'):
        install(linux)
    if platform == 'darwin':
        install(darwin)
