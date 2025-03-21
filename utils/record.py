import speech_recognition as sr
import tempfile

def record_audio(duration=None):
    RATE = 16000
    CHANNELS = 1
    
    recognizer = sr.Recognizer()
    recognizer.pause_threshold = 1.0  # Increased pause threshold
    recognizer.phrase_threshold = 0.3  # Adjust phrase threshold
    recognizer.non_speaking_duration = 0.5  # Time of silence needed to mark the end of a phrase
    
    microphone = sr.Microphone()
    
    print("Recording...")
    
    with microphone as source:
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        try:
            audio = recognizer.listen(source, 
                                    timeout=10,
                                    phrase_time_limit=None)
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio_file:
                temp_audio_file.write(audio.get_wav_data())
                return temp_audio_file.name
                
        except sr.WaitTimeoutError:
            print("No speech detected within timeout period.")
            return None