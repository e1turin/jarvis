import os
from typing import List
from openai import OpenAI, APIError, APITimeoutError, APIConnectionError
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()

SYSTEM_PROMPT = (
    "You are Jarvis (Джарвис), a voice AI assistant. "
    "Your name is Jarvis, pronounced 'Джарвис' in Russian. "
    "\n\n"
    "IMPORTANT CONTEXT:\n"
    "- The user is speaking to you with their voice. "
    "- Their speech is converted to text by an automatic speech recognition system. "
    "- Your response will be read aloud by a speech synthesizer (TTS). "
    "- You CAN hear them. You ARE in a conversation. Just respond naturally.\n"
    "\n"
    "RULES:\n"
    "1. PLAIN TEXT ONLY. Never use markdown, bold, italics, asterisks, "
    "   or any formatting. Your text is spoken aloud.\n"
    "2. No emojis. No bullet points. No numbered lists.\n"
    "3. Respond in the same language the user speaks to you.\n"
    "4. Keep responses concise and conversational, like a spoken dialogue.\n"
    "\n"
    "CONVERSATION CONTROL:\n"
    "If the conversation is naturally finished and the user has no more questions, "
    'end your response with "[END]". Do NOT use [END] if the user might have follow-up questions.'
)


class Message(BaseModel):
    role: str
    content: str


class ChatResult(BaseModel):
    text: str
    action: str = "continue"  # "continue" or "end"


class JarvisBrain:
    def __init__(self, model: str = None):
        provider = os.getenv("LLM_PROVIDER", "openai").lower()
        base_url = os.getenv("LLM_BASE_URL")
        api_key = os.getenv("LLM_API_KEY")
        model_name = model or os.getenv("LLM_MODEL") or "gpt-4o"

        client_kwargs = {
            "base_url": base_url,
            "timeout": 30.0,
            "max_retries": 1,
        }

        if provider == "lmstudio":
            client_kwargs["api_key"] = api_key or "lm-studio"
        else:
            client_kwargs["api_key"] = os.getenv("OPENAI_API_KEY") or api_key

        self.client = OpenAI(**client_kwargs)
        self.model = model_name

        self.history: List[Message] = [
            Message(role="system", content=SYSTEM_PROMPT)
        ]

    def chat(self, user_input: str) -> ChatResult:
        self.history.append(Message(role="user", content=user_input))
        messages = [msg.model_dump() for msg in self.history]

        try:
            print(f"🧠 Thinking...")

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=1024,
            )
            reply = response.choices[0].message.content

            # Check for [END] marker
            end_marker = "[END]"
            if reply.rstrip().endswith(end_marker):
                text = reply.rstrip()[:-len(end_marker)].strip()
                self.history.append(Message(role="assistant", content=text))
                return ChatResult(text=text, action="end")

            self.history.append(Message(role="assistant", content=reply))
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
