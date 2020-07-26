# coding: utf-8


from __future__ import print_function
import sys
import requests
import json
import time


class SpotifyException(Exception):
    def __init__(self, http_status, code, msg, headers=None):
        self.http_status = http_status
        self.code = code
        self.msg = msg
        # `headers` is used to support `Retry-After` in the event of a
        # 429 status code.
        if headers is None:
            headers = {}
        self.headers = headers

    def __str__(self):
        return 'http status: {0}, code:{1} - {2}'.format(
            self.http_status, self.code, self.msg)


class Spotify(object):
    '''
        Example usage::

            import spotipy

            urn = 'spotify:artist:3jOstUTkEu2JkjvRdBA5Gu'
            sp = spotipy.Spotify()

            sp.trace = True # turn on tracing
            sp.trace_out = True # turn on trace out

            artist = sp.artist(urn)
            print(artist)

            user = sp.user('plamere')
            print(user)
    '''

    trace = False  # Enable tracing?
    trace_out = False
    max_get_retries = 10

    def __init__(self, auth=None, requests_session=True,
        client_credentials_manager=None, proxies=None, requests_timeout=None):
        '''
        Create a Spotify API object.

        :param auth: An authorization token (optional)
        :param requests_session:
            A Requests session object or a truthy value to create one.
            A falsy value disables sessions.
            It should generally be a good idea to keep sessions enabled
            for performance reasons (connection pooling).
        :param client_credentials_manager:
            SpotifyClientCredentials object
        :param proxies:
            Definition of proxies (optional)
        :param requests_timeout:
            Tell Requests to stop waiting for a response after a given number of seconds
        '''
        self.prefix = 'https://api.spotify.com/v1/'
        self._auth = auth
        self.client_credentials_manager = client_credentials_manager
        self.proxies = proxies
        self.requests_timeout = requests_timeout

        if isinstance(requests_session, requests.Session):
            self._session = requests_session
        else:
            if requests_session:  # Build a new session.
                self._session = requests.Session()
            else:  # Use the Requests API module as a "session".
                from requests import api
                self._session = api

    def _auth_headers(self):
        if self._auth:
            return {'Authorization': 'Bearer {0}'.format(self._auth)}
        elif self.client_credentials_manager:
            token = self.client_credentials_manager.get_access_token()
            return {'Authorization': 'Bearer {0}'.format(token)}
        else:
            return {}

    def _internal_call(self, method, url, payload, params):
        args = dict(params=params)
        args["timeout"] = self.requests_timeout
        if not url.startswith('http'):
            url = self.prefix + url
        headers = self._auth_headers()
        headers['Content-Type'] = 'application/json'

        if payload:
            args["data"] = json.dumps(payload)

        if self.trace_out:
            print(url)
        r = self._session.request(method, url, headers=headers, proxies=self.proxies, **args)

        if self.trace:  # pragma: no cover
            print()
            print ('headers', headers)
            print ('http status', r.status_code)
            print(method, r.url)
            if payload:
                print("DATA", json.dumps(payload))

        try:
            r.raise_for_status()
        except:
            if r.text and len(r.text) > 0 and r.text != 'null':
                raise SpotifyException(r.status_code,
                    -1, '%s:\n %s' % (r.url, r.json()['error']['message']),
                    headers=r.headers)
            else:
                raise SpotifyException(r.status_code,
                    -1, '%s:\n %s' % (r.url, 'error'), headers=r.headers)
        finally:
            r.connection.close()
        if r.text and len(r.text) > 0 and r.text != 'null':
            results = r.json()
            if self.trace:  # pragma: no cover
                print('RESP', results)
                print()
            return results
        else:
            return None

    def _get(self, url, args=None, payload=None, **kwargs):
        if args:
            kwargs.update(args)
        retries = self.max_get_retries
        delay = 1
        while retries > 0:
            try:
                return self._internal_call('GET', url, payload, kwargs)
            except SpotifyException as e:
                retries -= 1
                status = e.http_status
                # 429 means we hit a rate limit, backoff
                if status == 429 or (status >= 500 and status < 600):
                    if retries < 0:
                        raise
                    else:
                        sleep_seconds = int(e.headers.get('Retry-After', delay))
                        print ('retrying ...' + str(sleep_seconds) + 'secs')
                        time.sleep(sleep_seconds)
                        delay += 1
                else:
                    raise
            except Exception as e:
                raise
                print('exception', str(e))
                # some other exception. Requests have
                # been know to throw a BadStatusLine exception
                retries -= 1
                if retries >= 0:
                    sleep_seconds = int(e.headers.get('Retry-After', delay))
                    print ('retrying ...' + str(delay) + 'secs')
                    time.sleep(sleep_seconds)
                    delay += 1
                else:
                    raise

    def _post(self, url, args=None, payload=None, **kwargs):
        if args:
            kwargs.update(args)
        return self._internal_call('POST', url, payload, kwargs)

    def _delete(self, url, args=None, payload=None, **kwargs):
        if args:
            kwargs.update(args)
        return self._internal_call('DELETE', url, payload, kwargs)

    def _put(self, url, args=None, payload=None, **kwargs):
        if args:
            kwargs.update(args)
        return self._internal_call('PUT', url, payload, kwargs)

    def next(self, result):
        ''' returns the next result given a paged result

            Parameters:
                - result - a previously returned paged result
        '''
        if result['next']:
            return self._get(result['next'])
        else:
            return None

    def previous(self, result):
        ''' returns the previous result given a paged result

            Parameters:
                - result - a previously returned paged result
        '''
        if result['previous']:
            return self._get(result['previous'])
        else:
            return None

    def _warn(self, msg):
        print('warning:' + msg, file=sys.stderr)

    def user(self, user):
        ''' Gets basic profile information about a Spotify User

            Parameters:
                - user - the id of the usr
        '''
        return self._get('users/' + user)

    def current_user_playing_track(self):
        ''' Get information about the current users currently playing track.
        '''
        return self._get('me/player/currently-playing')

    def me(self):
        ''' Get detailed profile information about the current user.
            An alias for the 'current_user' method.
        '''
        return self._get('me/')

    def _get_id(self, type, id):
        fields = id.split(':')
        if len(fields) >= 3:
            if type != fields[-2]:
                self._warn('expected id of type %s but found type %s %s',
                           type, fields[-2], id)
            return fields[-1]
        fields = id.split('/')
        if len(fields) >= 3:
            itype = fields[-2]
            if type != itype:
                self._warn('expected id of type %s but found type %s %s',
                           type, itype, id)
            return fields[-1]
        return id

    def _get_uri(self, type, id):
        return 'spotify:' + type + ":" + self._get_id(type, id)
