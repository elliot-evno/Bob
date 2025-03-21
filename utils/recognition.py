import speech_recognition as sr
import threading
from ..openai.whisper import *
from ..openai.whisper import *
from .record import *
from fuzzywuzzy import fuzz



def listen_for_interrupt():
    global mhm_stop_speech, answer_stop_speech
    recognizer = sr.Recognizer()
    microphone = sr.Microphone()
   
    try:
        with microphone as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.2)
            try:
                audio = recognizer.listen(source, phrase_time_limit=1)
                text = recognizer.recognize_google(audio, show_all=False).lower()
                if "bob" in text:
                    print("Interrupt detected!")
                    with speech_lock:
                        mhm_stop_speech = True
                        answer_stop_speech = True
                    
                    # Say "Mhm?" just like with wake word detection
                    with speech_lock:
                        mhm_stop_speech = False
                    mhm_thread = threading.Thread(target=text_to_speech, args=("Mhm?", "mhm"))
                    mhm_thread.start()

                    # Record and process new question after interrupt
                    audio_file_path = record_audio()
                    if audio_file_path:
                        question_text = transcribe_audio(audio_file_path)
                        print(f"Transcribed question: '{question_text}'")
                        return question_text
                    else:
                        print("No audio recorded")
                        return None
            except sr.UnknownValueError:
                return None
            except sr.RequestError:
                return None
    except Exception as e:
        print(f"Error in interrupt listener: {e}")
        return None















def is_wake_word(text, wake_word="bob", threshold=70):  # Lowered threshold
    if not text:
        return False
        
    text = text.lower()
    words = text.split()
    
    # Check each word and nearby word combinations
    for i in range(len(words)):
        # Direct match
        if wake_word in words[i]:
            return True
            
        # Fuzzy match current word
        similarity = fuzz.ratio(words[i], wake_word)
        if similarity >= threshold:
            return True
        
        # Check word combinations (helps with merged words)
        if i < len(words) - 1:
            two_words = f"{words[i]}{words[i+1]}"
            similarity = fuzz.ratio(two_words, wake_word)
            if similarity >= threshold:
                return True
    
    return False
