import time
from jarvis.brain import JarvisBrain
from jarvis.listener import Listener
from jarvis.speaker import Speaker
from jarvis.wake import WakeWordDetector
from jarvis.sounds import play_listen_sound, play_thinking_ticks, stop_thinking_ticks
from jarvis.config import settings


def main():
    print("--- Jarvis Voice AI Assistant ---")
    print("Initializing modules...")

    brain = JarvisBrain()
    listener = Listener()
    speaker = Speaker()

    print(f"System ready. Provider: {settings.llm_provider} | Model: {brain.model}")

    # Create a wake word detector for barge-in (shared model)
    barge_detector = WakeWordDetector() if settings.wake_mode else None

    if settings.wake_mode:
        # Main wake word detector for initial activation
        wake_detector = WakeWordDetector()
        print("Say 'Jarvis' or 'Джарвис' to wake me up.")
    else:
        wake_detector = None

    while True:
        try:
            # --- Wait for wake word ---
            if settings.wake_mode and wake_detector:
                detected = wake_detector.wait_for_wake_word()
                if not detected:
                    break
                # Pass pre-wake buffer to listener so speech before/during wake word isn't lost
                listener.set_pre_wake(wake_detector.get_pre_buffer_file())

            # --- Conversation mode with barge-in ---
            play_listen_sound()
            print("🎙️ Conversation started. Say 'Джарвис' to interrupt me.\n")

            last_activity = time.time()
            should_sleep = False

            while not should_sleep:
                # Listen
                audio_file = listener.record_audio()
                user_text = listener.transcribe(audio_file)

                if not user_text:
                    if time.time() - last_activity >= settings.conversation_timeout:
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
                play_thinking_ticks()
                result = brain.chat(user_text)
                stop_thinking_ticks()

                if result.action == "end":
                    speaker.speak(result.text)
                    print("💤 LLM ended the conversation.\n")
                    should_sleep = True
                    break

                # --- Speak with barge-in support ---
                print(f"Jarvis: {result.text}")

                if settings.tts_backend == "print":
                    print()
                    continue

                # Generate audio
                file_path = speaker.generate_speech(result.text)
                if not file_path:
                    print()
                    continue

                # Check if response contains wake words (would cause self-interruption via echo)
                response_mentions_wake = False
                if barge_detector and result.text:
                    text_lower = result.text.lower()
                    response_mentions_wake = any(ww in text_lower for ww in barge_detector.wake_words)

                # Play and monitor for barge-in (persistent stream, no blinking)
                speaker.play_async(file_path)
                interrupted = False

                if barge_detector and speaker.is_playing() and not response_mentions_wake:
                    interrupted = barge_detector.wait_for_barge_in(speaker.is_playing)

                if interrupted:
                    speaker.stop_playback()
                    print("⏹️ Interrupted!\n")
                else:
                    # Wait for playback to finish
                    if speaker.playback_process:
                        speaker.playback_process.wait()
                    print()

        except KeyboardInterrupt:
            print("\nShutting down...")
            break
        except Exception as e:
            print(f"Unexpected error: {e}")
            break


if __name__ == "__main__":
    main()
