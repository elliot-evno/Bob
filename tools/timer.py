import threading
import datetime
import pygame
from ..openai.whisper import *




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
