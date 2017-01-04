# KEX.Py

The Seattle radio station KEXP (90.3) limits the availability of archived programs, making it difficult to meaninfully "binge" on them. Playlists remain available, though, and much of the music can be found on Spotify. Use KEX.Py to publish Spotify playlists based on past KEXP programming.

## Installation and Setup

```bash
$ git clone ...
$ cd KEX.Py
$ pip3 install -r requirements.txt
```

Obtain a Spotify client ID and secret from https://developer.spotify.com/my-applications/ -- Use this information to set the corresponding environment variables in ```spotipy-env.sh```

## Running KEX.Py

The KEXP program Shake the Shack airs every Friday between six and nine. To build a playlist entitled "Shake the Shack" from the December 30th KEXP playlist, run the following:

```
$ source spotipy-env.sh
$ ./KEX.Py --username <your-username> --playlist "Shake the Shack" --mdy 12/30/2016 --hour 18-21
```


