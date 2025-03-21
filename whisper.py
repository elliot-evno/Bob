from openaiclient import client
import os
import pygame
import threading
import io
speech_lock = threading.Lock()


def transcribe_audio(audio_file_path):
    try:
        with open(audio_file_path, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
        return transcription.text
    finally:
        # Clean up the temporary file
        os.unlink(audio_file_path)


def text_to_speech(text: str, stop_flag: str):
    global mhm_stop_speech, answer_stop_speech

    # Use OpenAI's Text-to-Speech API
    response = client.audio.speech.create(
        model="tts-1",
        voice="alloy",
        input=text
    )
   
    # Load audio into memory using BytesIO
    mp3_data = io.BytesIO(response.content)
   
    # Initialize the mixer if not already initialized
    if not pygame.mixer.get_init():
        pygame.mixer.init()
   
    # Load the audio from memory
    pygame.mixer.music.load(mp3_data, 'mp3')
    pygame.mixer.music.play()
   
    # Wait until the audio finishes playing or is interrupted
    while pygame.mixer.music.get_busy():
        with speech_lock:
            if stop_flag == "mhm" and mhm_stop_speech:
                pygame.mixer.music.stop()
                break
            elif stop_flag == "answer" and answer_stop_speech:
                pygame.mixer.music.stop()
                break
        pygame.time.Clock().tick(10)
   
    # Stop the music if it's still playing
    pygame.mixer.music.stop()

