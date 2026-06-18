import os
import time
from jarvis.brain import JarvisBrain
from jarvis.listener import Listener
from jarvis.speaker import Speaker
from jarvis.wake import WakeWordDetector


def main():
    print("--- Jarvis Voice AI Assistant ---")
    print("Initializing modules...")

    brain = JarvisBrain()
    listener = Listener()
    speaker = Speaker()

    wake_mode = os.getenv("WAKE_MODE", "true").lower() == "true"
    conversation_timeout = int(os.getenv("CONVERSATION_TIMEOUT", "30"))

    print(f"System ready. Provider: {os.getenv('LLM_PROVIDER')} | Model: {brain.model}")

    if wake_mode:
        detector = WakeWordDetector()
        print("Say 'Jarvis' or 'Джарвис' to wake me up.")
    else:
        detector = None

    while True:
        try:
            # --- Step 1: Wait for wake word ---
            if wake_mode and detector:
                detected = detector.wait_for_wake_word()
                if not detected:
                    break

            # --- Step 2: Conversation mode ---
            print("🎙️ Conversation started. I'll stay awake.")
            print(f"   Say 'пока' or be silent for {conversation_timeout}s to end.\n")

            last_activity = time.time()
            should_sleep = False

            while not should_sleep:
                audio_file = listener.record_audio()
                user_text = listener.transcribe(audio_file)

                if not user_text:
                    if time.time() - last_activity >= conversation_timeout:
                        print("💤 Timeout — going back to sleep.\n")
                        should_sleep = True
                    continue

                last_activity = time.time()

                # Check for sleep commands
                sleep_words = {"пока", "до свидания", "всё", "свободен",
                               "bye", "goodbye", "спать", "иди спать", "отдыхай",
                               "закончили", "хватит"}
                if user_text.strip().lower() in sleep_words:
                    speaker.speak("Хорошо. Позовите, если понадоблюсь.")
                    print("💤 Going to sleep on request.\n")
                    should_sleep = True
                    break

                print(f"You: {user_text}")
                result = brain.chat(user_text)
                speaker.speak(result.text)

                if result.action == "end":
                    print("💤 LLM ended the conversation.\n")
                    should_sleep = True

                print()

        except KeyboardInterrupt:
            print("\nShutting down...")
            break
        except Exception as e:
            print(f"Unexpected error: {e}")
            break


if __name__ == "__main__":
    main()
