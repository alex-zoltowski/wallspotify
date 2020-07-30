# WallSpotify
Desktop application that dynamically sets the desktop wallpaper image to the album art of your currently playing Spotify song.

## Releases

[Download for Windows](WallSpotify.exe)

[Download for MacOS](WallSpotify-MacOS.zip) 

## Usage
- Python 3.8+
- Install dependencies using `python install.py`
- Spotify Developer App (Create one by logging into the Spotify Developer Dashboard)
- Create a file in the `src/` directory called: `spotify_config.py`
- Add the lines:
```
client_id = 'YOUR SPOTIFY CLIENT_ID'
client_secret = 'YOUR SPOTIFY CLIENT_SECRET'
redirect_uri = 'YOUR SPOTIFY REDIRECT_URI'
```

## Other
- Run the program with `python wallspotify.py`
- Build an executable `python build_executable.py`
- Executables are placed in `dist/`

## Windows Only
- After building and running a .exe, it will add a Registry Key to enable running the app on start up.
- You can remove this key by running `python remove_reg_key.py`


