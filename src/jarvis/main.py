"""
Main orchestrator — ties together wake detection, conversation, and TTS.
"""

import time
import threading
from jarvis.brain import ConversationManager
from jarvis.listener import Listener
from jarvis.speaker import Speaker
from jarvis.wake import WakeWordDetector
from jarvis.sounds import play_listen_sound, play_thinking_ticks, stop_thinking_ticks
from jarvis.config import settings


def main():
    name = settings.agent_name
    wake = settings.wake_word_display

    print(f"--- {name} Voice AI Assistant ---")
    print("Initializing modules...")

    brain = ConversationManager()
    listener = Listener()
    speaker = Speaker()

    print(f"System ready. Provider: {brain.llm.provider_label} | Model: {brain.llm.model} | Built-in tools: web_search")

    # Create wake word detectors
    barge_detector = WakeWordDetector() if settings.wake_mode else None

    if settings.wake_mode:
        wake_detector = WakeWordDetector()
        print(f"Say '{wake}' to wake me up.")
    else:
        wake_detector = None

    while True:
        try:
            # --- Wait for wake word ---
            if settings.wake_mode and wake_detector:
                detected = wake_detector.wait_for_wake_word()
                if not detected:
                    break
                listener.set_pre_wake(wake_detector.get_pre_buffer_file())

            # --- Conversation mode with barge-in ---
            play_listen_sound()
            print(f"🎙️ Conversation started. Say '{wake}' to interrupt me.\n")

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
                sleep_words = {w.strip().lower() for w in settings.sleep_words.split(",")}
                if user_text.strip().lower() in sleep_words:
                    speaker.speak("Хорошо. Позовите, если понадоблюсь.")
                    print("💤 Going to sleep on request.\n")
                    should_sleep = True
                    break

                print(f"You: {user_text}")
                play_thinking_ticks()

                # ── Think with barge-in ───────────────────────────────────────
                thinking_done = threading.Event()
                thinking_result = [None]

                def _think():
                    r = brain.send_message(user_text)
                    thinking_result[0] = r
                    thinking_done.set()

                think_thread = threading.Thread(target=_think, daemon=True)
                think_thread.start()

                interrupted = False
                if barge_detector:
                    interrupted = barge_detector.wait_for_barge_in(
                        lambda: think_thread.is_alive()
                    )

                if interrupted:
                    stop_thinking_ticks()
                    print("⏹️ Interrupted!\n")
                    continue

                # Thinking completed normally
                thinking_done.wait()
                stop_thinking_ticks()
                result = thinking_result[0]

                # ── Handle errors: print, skip TTS, skip history, keep listening ──
                if result.is_error:
                    print(f"❌ {result.text}\n")
                    continue

                # Commit to history (only if not interrupted)
                brain.commit_turn(user_text, result)

                if result.action == "end":
                    print(f"{name}: {result.text}")
                    speaker.speak(result.text)
                    print("💤 LLM ended the conversation.\n")
                    should_sleep = True
                    break

                # --- Speak with barge-in support ---
                print(f"{name}: {result.text}")

                if settings.tts_backend == "print":
                    print()
                    continue

                # Check if response contains wake words (echo protection)
                response_mentions_wake = False
                if barge_detector and result.text:
                    text_lower = result.text.lower()
                    response_mentions_wake = any(
                        ww in text_lower for ww in barge_detector.wake_words
                    )

                if barge_detector and not response_mentions_wake:
                    # ── Non-blocking: generate TTS in background thread ──────
                    gen_done = threading.Event()

                    def _gen_and_play():
                        fp = speaker.generate_speech(result.text)
                        if fp and not speaker._cancelled:
                            speaker.play_async(fp)
                        gen_done.set()

                    gen_thread = threading.Thread(target=_gen_and_play, daemon=True)
                    gen_thread.start()

                    # Monitor for wake word during generation AND playback
                    interrupted = barge_detector.wait_for_barge_in(
                        lambda: gen_thread.is_alive() or speaker.is_playing()
                    )

                    if interrupted:
                        speaker.stop_playback()
                        print("⏹️ Interrupted!\n")
                    else:
                        gen_done.wait(timeout=10)
                        speaker.player.wait()
                        print()
                else:
                    if response_mentions_wake:
                        print("  (blocking mode — response mentions wake word)")
                    # ── Blocking mode: no barge-in ──────────────────────────
                    file_path = speaker.generate_speech(result.text)
                    if file_path:
                        speaker.play_async(file_path)
                        speaker.player.wait()
                    print()

        except KeyboardInterrupt:
            print("\nShutting down...")
            break
        except Exception as e:
            print(f"Unexpected error: {e}")
            break


if __name__ == "__main__":
    main()
