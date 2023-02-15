import winreg


name = 'wallspotify'
registry = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
key = winreg.OpenKey(registry, r'SOFTWARE\Microsoft\Windows\CurrentVersion\Run', 0, winreg.KEY_ALL_ACCESS)

winreg.DeleteValue(key, name)
winreg.CloseKey(key)
