import pip

_all_ = [
    "PyQt5>=5.12.2",
    "Pillow>=7.2.0",
    "requests>=2.24.0",
    "pyinstaller>=3.6",
]

windows = []

linux = []

darwin = ["appscript>=1.1.0",]

def install(packages):
    for package in packages:
        pip.main(['install', package])

if __name__ == '__main__':

    from sys import platform

    install(_all_)
    if platform == 'windows':
        install(windows)
    if platform.startswith('linux'):
        install(linux)
    if platform == 'darwin':
        install(darwin)
