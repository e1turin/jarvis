from typing import List
from openai import OpenAI, APIError, APITimeoutError, APIConnectionError
from pydantic import BaseModel
from jarvis.config import settings


class Message(BaseModel):
    role: str
    content: str


class ChatResult(BaseModel):
    text: str
    action: str = "continue"  # "continue" or "end"


class JarvisBrain:
    def __init__(self, model: str = None):
        self.client = OpenAI(
            base_url=settings.llm_base_url or None,
            api_key=settings.llm_api_key,
            timeout=30.0,
            max_retries=1,
        )
        self.model = model or settings.llm_model

        system_prompt = settings.load_system_prompt()
        self.history: List[Message] = [
            Message(role="system", content=system_prompt)
        ]

    def send_message(self, user_input: str) -> ChatResult:
        """
        Send user input to the LLM and get a response.
        Does NOT modify self.history — caller must call commit_turn() on success.
        This allows the caller to discard the turn if interrupted.
        """
        # Build messages from history + new input, without modifying history
        messages = [msg.model_dump() for msg in self.history]
        messages.append({"role": "user", "content": user_input})

        try:
            print(f"🧠 Thinking...")

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=settings.llm_temperature,
                max_tokens=settings.llm_max_tokens,
            )
            reply = response.choices[0].message.content

            # Check for [END] marker
            end_marker = "[END]"
            if reply.rstrip().endswith(end_marker):
                text = reply.rstrip()[:-len(end_marker)].strip()
                return ChatResult(text=text, action="end")

            return ChatResult(text=reply, action="continue")

        except APIConnectionError:
            return ChatResult(
                text="Could not connect to the LLM server. Is LM Studio running and the server started?",
                action="end"
            )
        except APITimeoutError:
            return ChatResult(
                text="LLM request timed out. The model may still be loading.",
                action="end"
            )
        except APIError as e:
            return ChatResult(text=f"LLM Error: {e}", action="end")
        except Exception as e:
            return ChatResult(text=f"Unexpected error: {str(e)}", action="end")

    def commit_turn(self, user_input: str, result: ChatResult):
        """
        Commit a completed turn to conversation history.
        Call this only after send_message() succeeds and was not interrupted.
        """
        self.history.append(Message(role="user", content=user_input))
        self.history.append(Message(role="assistant", content=result.text))

    def chat(self, user_input: str) -> ChatResult:
        """
        Original chat method — sends message AND commits to history.
        Kept for backward compatibility (used by standalone test).
        """
        result = self.send_message(user_input)
        self.commit_turn(user_input, result)
        return result


if __name__ == "__main__":
    brain = JarvisBrain()
    print(f"Jarvis Brain initialized | Model: {brain.model}")
    print("Type 'quit' to exit.")
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["quit", "exit", "bye"]:
            break
        result = brain.chat(user_input)
        print(f"Jarvis: {result.text}")
        if result.action == "end":
            print("(END)")
