# Grew tired of Google Home saying that it didn't understand me so I built this guy who is a lot more understanding though dull at times when calling his name.

### To run: 
1. Get an openai, elevenlabs api key.
2. Create a spotify dev account and setup an app.
3. Set the redirect uri in your spotify app to "http://localhost:8888/callback".
4. Get the client id and client secret from spotify.

### Then just run:
 ```bash
pip install sounddevice wave numpy pygame SpeechRecognition fuzzywuzzy duckduckgo-search spotipy platformdirs
```
 ```bash
python main.py
```
