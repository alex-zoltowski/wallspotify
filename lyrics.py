from lyricsgenius import Genius
from spotipy import Spotify
from spotipy.oauth2 import SpotifyClientCredentials
from src import spotify_config


client_credentials_manager = SpotifyClientCredentials(spotify_config.client_id, spotify_config.client_secret)
sp = Spotify(client_credentials_manager=client_credentials_manager)

genius = Genius(spotify_config.lyricgenius_access_code)

song_name = input("Enter the name of the song: ")
artist_name = input("Enter the name of the artist: ")

results = sp.search(q='track:{} artist:{}'.format(song_name, artist_name), type='track')

track_id = results['tracks']['items'][0]['id']

song = genius.search_song(song_name, artist_name)

if song:
    print("Lyrics for {} by {}".format(song.title, song.artist))
    print(song.lyrics)
else:
    print("No lyrics found for {} by {}".format(song_name, artist_name))