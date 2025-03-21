import threading
from collections import deque

volume_stack = deque()




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

