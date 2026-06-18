import os
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
    input_mode = os.getenv("INPUT_MODE", "vad").lower()

    print(f"System ready. Provider: {os.getenv('LLM_PROVIDER')} | Model: {brain.model}")

    if wake_mode:
        detector = WakeWordDetector()
        print("Say 'Jarvis' or 'Джарвис' to activate.")
    else:
        detector = None
        print(f"Input mode: {input_mode.upper()}")

    while True:
        try:
            # --- Wait for wake word (if enabled) ---
            if wake_mode and detector:
                detected = detector.wait_for_wake_word()
                if not detected:
                    break  # User pressed Ctrl+C

            # --- Conversation mode ---
            if input_mode == "key":
                input("⏎ Press Enter to speak...")

            audio_file = listener.record_audio()
            user_text = listener.transcribe(audio_file)

            if not user_text:
                continue

            print(f"You: {user_text}")

            reply = brain.chat(user_text)
            speaker.speak(reply)

        except KeyboardInterrupt:
            print("\nShutting down...")
            break
        except Exception as e:
            print(f"Unexpected error: {e}")
            break


if __name__ == "__main__":
    main()
