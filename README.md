# WallSpotify
Desktop application that dynamically sets the desktop wallpaper image to the album art of your currently playing Spotify song.

## Requirements
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
## Build Executable

`python build_executable.py`

Executables are placed in `dist/`


