import tempfile
import speech_recognition as sr
import pygame
import threading
import time
from duckduckgo_search import DDGS
import datetime
import spotipy
import platform
import subprocess
from fuzzywuzzy import fuzz
from spotify import *
from whisper import *
from openai import *


# Initialize pygame mixer for audio playback
pygame.mixer.init()

# Add these global variables
timer_active = False
timer_sound_thread = None
notification_sound = None  # Global variable to store the Sound object
speech_thread = None
stop_speech = False
currently_playing = False
current_volume = 80  # Change this value to set the default volume
temp_volume_reduction = 0  # To keep track of temporary volume reduction




# New global variables for separate speech flags and lock
speech_lock = threading.Lock()
mhm_stop_speech = False
answer_stop_speech = False


# Add these constants near other global variables
ENERGY_THRESHOLD = 1000  # Adjust based on your microphone
DYNAMIC_ENERGY_RATIO = 1.5
RECORD_TIMEOUT = 2  # Seconds to wait before processing audio
PHRASE_TIMEOUT = 3  # Seconds to wait for a complete phrase




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




def adjust_volume(new_volume):
    global current_volume, sp
    current_volume = max(0, min(100, new_volume))
    if sp is not None:
        try:
            sp.volume(current_volume)
            print(f"Volume set to {current_volume}%")
        except Exception as e:
            print(f"Error adjusting Spotify volume: {e}")
    return f"Volume set to {current_volume}%"



def lower_volume():
    global current_volume, sp
    if sp is not None:
        try:
            volume_stack.append(current_volume)
            new_volume = max(0, current_volume - 30)
            sp.volume(new_volume)
            print(f"Spotify volume temporarily lowered to {new_volume}%")
        except Exception as e:
            print(f"Error adjusting Spotify volume: {e}")

def restore_volume():
    global current_volume, sp
    if sp is not None and volume_stack:
        try:
            previous_volume = volume_stack.pop()
            if previous_volume != current_volume:  # Only restore if it's different
                sp.volume(current_volume)
                print(f"Spotify volume set to current volume: {current_volume}%")
            else:
                print(f"Spotify volume unchanged: {current_volume}%")
        except Exception as e:
            print(f"Error setting Spotify volume: {e}")






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








def set_timer_or_alarm(type, value, callback):
    if type == "timer":
        timer = threading.Timer(value, callback)
        timer.start()
        return f"Timer set for {value} seconds."
    elif type == "alarm":
        now = datetime.datetime.now()
        alarm_time = datetime.datetime.strptime(value, "%H:%M").replace(year=now.year, month=now.month, day=now.day)
        if alarm_time <= now:
            alarm_time += datetime.timedelta(days=1)
        delay = (alarm_time - now).total_seconds()
        timer = threading.Timer(delay, callback)
        timer.start()
        return f"Alarm set for {value}."




def timer_alarm_callback():
    global timer_active, timer_sound_thread
    print("Timer or alarm finished!")
    text_to_speech("Your timer or alarm has finished!", "answer")
    timer_active = True
    timer_sound_thread = threading.Thread(target=play_timer_sound)
    timer_sound_thread.start()




def play_timer_sound():
    global timer_active, notification_sound
    pygame.mixer.init()
    notification_sound = pygame.mixer.Sound(r"PATH_TO_SOUND")
    notification_sound.set_volume(1.0)  # Set initial volume to 100%
    while timer_active:
        notification_sound.play()
        pygame.time.wait(2000)  # Wait for 2 seconds between plays







def perform_search(query, num_results=3):
    with DDGS() as ddgs:
        results = list(ddgs.text(query, max_results=num_results))
    return results






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




def main():
    global timer_active, timer_sound_thread, notification_sound, speech_thread, stop_speech, currently_playing, current_volume, temp_volume_reduction
    global mhm_stop_speech, answer_stop_speech, sp, current_volume
    
    # Initialize Spotify client
    try:
        token_info = authorize_spotify()
        sp = spotipy.Spotify(auth_manager=auth_manager)
        print("Successfully authenticated with Spotify!")
        
        # Check for and initialize Spotify device
        devices = sp.devices()
        if not devices['devices']:
            print("No Spotify devices found. Attempting to launch Spotify client...")
            if platform.system() == "Windows":
                subprocess.Popen(["start", "spotify:"], shell=True)
            elif platform.system() == "Darwin":  # macOS
                subprocess.Popen(["open", "-a", "Spotify"])
            elif platform.system() == "Linux":
                subprocess.Popen(["spotify"])
            
            # Wait for Spotify to launch
            max_attempts = 10
            for attempt in range(max_attempts):
                time.sleep(2)
                devices = sp.devices()
                if devices['devices']:
                    print("Spotify client launched successfully!")
                    break
                if attempt == max_attempts - 1:
                    print("Could not find or launch Spotify. Please make sure Spotify is installed.")
        
        # Only set volume if we have an active device
        if devices['devices']:
            device_id = devices['devices'][0]['id']
            sp.transfer_playback(device_id=device_id, force_play=False)
            time.sleep(1)  # Wait for device activation
            sp.volume(current_volume)
            print(f"Spotify initialized with volume {current_volume}%")
    except Exception as e:
        print(f"Failed to initialize Spotify client: {e}")
        sp = None

    recognizer = sr.Recognizer()
    recognizer.energy_threshold = ENERGY_THRESHOLD
    recognizer.dynamic_energy_threshold = True
    recognizer.dynamic_energy_adjustment_damping = 0.15
    recognizer.dynamic_energy_ratio = DYNAMIC_ENERGY_RATIO
    recognizer.pause_threshold = 0.8  # Shorter pause threshold
    recognizer.operation_timeout = None  # No timeout for operations
    
    microphone = sr.Microphone()

    print("Listening for 'bob'...")

    while True:
        try:
            with microphone as source:
                # Calibrate for ambient noise, including music if playing
                if currently_playing:
                    print("Music playing - adjusting sensitivity...")
                    recognizer.adjust_for_ambient_noise(source, duration=1)
                    recognizer.energy_threshold *= 0.8  # Make more sensitive when music is playing
                else:
                    recognizer.adjust_for_ambient_noise(source, duration=0.5)
                
                print("Listening...")
                audio = recognizer.listen(
                    source,
                    timeout=RECORD_TIMEOUT,
                    phrase_time_limit=PHRASE_TIMEOUT
                )

            try:
                text = recognizer.recognize_google(audio, show_all=False).lower()
                print(f"Heard: {text}")

                if is_wake_word(text):
                    print("Wake word detected!")
                    if currently_playing:
                        lower_volume()
                    
                    print("Wake word detected! Listening for your question...")
                    if timer_active and notification_sound:
                        print("Timer is active. Lowering notification volume.")
                        notification_sound.set_volume(0.4)  # Set volume to 40%
                    
                    # Always say "Mhm?" when wake word is detected in a separate thread
                    with speech_lock:
                        mhm_stop_speech = False
                    mhm_thread = threading.Thread(target=text_to_speech, args=("Mhm?", "mhm"))
                    mhm_thread.start()

                    audio_file_path = record_audio()
                    if audio_file_path:
                        question_text = transcribe_audio(audio_file_path)
                        print(f"Transcribed question: '{question_text}'")
                    else:
                        print("No audio recorded")
                        continue

                    # Check if the transcribed question is empty or contains only punctuation
                    if not question_text.strip() or question_text.strip() in '.,!?;:':
                        print("Transcribed question is empty or contains only punctuation. Dismissing.")
                        with speech_lock:
                            answer_stop_speech = False
                        dismiss_thread = threading.Thread(target=text_to_speech, args=("I didn't catch that. Could you please repeat?", "answer"))
                        dismiss_thread.start()
                        dismiss_thread.join()
                        with speech_lock:
                            answer_stop_speech = True
                        continue  # Go back to listening for 'bob'

                    if timer_active:
                        print("Timer is active. Checking if user wants to end it.")
                        timer_action = check_timer_end(question_text)
                        if "end timer" in timer_action:
                            print("User wants to end the timer. Stopping timer.")
                            timer_active = False
                            if timer_sound_thread:
                                timer_sound_thread.join()
                            with speech_lock:
                                answer_stop_speech = False
                            end_timer_thread = threading.Thread(target=text_to_speech, args=("Timer ended.", "answer"))
                            end_timer_thread.start()
                            end_timer_thread.join()
                            with speech_lock:
                                answer_stop_speech = True
                            continue  # Go back to listening for 'bob'

                    # Process the question
                    current_time = datetime.datetime.now().strftime("%I:%M %p")
                    timer_or_alarm = check_timer_or_alarm(question_text)
                    music_request = check_music_request(question_text)
                    volume_request = check_volume_request(question_text)

                    if volume_request:
                        new_volume = max(0, min(100, current_volume + (20 if volume_request == "up" else -20)))
                        answer = adjust_volume(new_volume)
                        volume_stack.clear()  # Clear the stack when volume is manually adjusted
                    elif timer_or_alarm:
                        type, value = timer_or_alarm
                        answer = set_timer_or_alarm(type, value, timer_alarm_callback)
                    elif music_request:
                        action, content = music_request
                        if action == "play":
                            # Directly try to play the song/artist
                            answer = play_spotify_song(content)
                        elif action == "search":
                            # Handle song identification requests
                            search_query = generate_search_query(f"song {content}")
                            search_results = perform_search(search_query)
                            answer = summarize_search_results(question_text, search_results, current_time)
                        elif action == "stop":
                            answer = stop_spotify_playback()
                            # Add a delay to allow the user to hear the lowered volume
                            time.sleep(2)
                    else:
                        # For general questions, perform a web search and summarize results
                        search_query = generate_search_query(question_text)
                        search_results = perform_search(search_query)
                        answer = summarize_search_results(question_text, search_results, current_time)

                    print(f"Answer: {answer}")
                    
                    # Start answer speech in a separate thread
                    with speech_lock:
                        answer_stop_speech = False
                    answer_thread = threading.Thread(target=text_to_speech, args=(answer, "answer"))
                    answer_thread.start()
                    
                    # Listen for interrupts while speaking
                    interrupt_thread = threading.Thread(target=listen_for_interrupt)
                    interrupt_thread.start()
                    
                    # Wait for answer speech to finish or be interrupted
                    answer_thread.join()
                    with speech_lock:
                        answer_stop_speech = True
                        mhm_stop_speech = True
                    
                    # Get new question if interrupt occurred
                    if interrupt_thread.is_alive():
                        new_question = interrupt_thread.join(timeout=0.1)
                        if new_question:
                            question_text = new_question  # Process the new question
                            # Stop the current interrupt thread before continuing
                            with speech_lock:
                                mhm_stop_speech = True
                                answer_stop_speech = True
                            continue  # Skip the volume restoration and continue processing

                    # Clean up any remaining threads
                    if interrupt_thread.is_alive():
                        interrupt_thread.join(timeout=0.1)

                    # Always attempt to restore volume after processing the request
                    if currently_playing:
                        restore_volume()

                    if timer_active and notification_sound:
                        print("Restoring notification volume.")
                        notification_sound.set_volume(1.0)  # Set volume back to 100%

                    print("Listening for 'bob'...")

            except sr.UnknownValueError:
                # No speech detected, continue listening
                continue
                
        except sr.WaitTimeoutError:
            # Timeout occurred, continue listening
            continue
        except Exception as e:
            print(f"Error: {e}")
            continue




if __name__ == "__main__":
    main()



