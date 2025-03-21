# Bob - Your Understanding AI Assistant

A voice-controlled AI assistant that's more flexible than Google Home. Built with OpenAI, Spotify, and speech recognition.

## Setup

1. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

2. Create `.env` file with:
```bash
OPENAI_API_KEY=your_openai_key
SPOTIPY_CLIENT_ID=your_spotify_client_id
SPOTIPY_CLIENT_SECRET=your_spotify_client_secret
SPOTIPY_REDIRECT_URI="http://localhost:8888/callback"
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run:
```bash
python main.py
```

## Features
- Voice commands with wake word "Bob"
- Spotify music control
- Timers & alarms
- Web search
- Volume control
