import os
import sys
from typing import Optional
from jarvis.brain import JarvisBrain
from jarvis.listener import Listener
from jarvis.speaker import Speaker

def main():
    print("--- Jarvis Voice AI Assistant ---")
    print("Initializing modules...")
    
    brain = JarvisBrain()
    listener = Listener()
    speaker = Speaker()
    
    print("System ready. Say something!")
    
    while True:
        try:
            # 1. Listen
            audio_file = listener.record_audio()
            
            # 2. Transcribe
            user_text = listener.transcribe(audio_file)
            
            if not user_text:
                continue
                
            print(f"You: {user_text}")
            
            # 3. Think
            reply = brain.chat(user_text)
            
            # 4. Speak
            speaker.speak(reply)
            
        except KeyboardInterrupt:
            print("\nShutting down...")
            break
        except Exception as e:
            print(f"Unexpected error: {e}")
            break

if __name__ == "__main__":
    # Add the current directory to the python path so we can import from jarvis
    sys.path.append(os.path.abspath(os.path.dirname(__file__)))
    main()
