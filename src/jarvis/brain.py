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
    "CRITICAL RULES for voice output:\n"
    "1. PLAIN TEXT ONLY. Never use markdown, bold, italics, asterisks, "
    "   or any formatting symbols. The text is read aloud by a speech synthesizer.\n"
    "2. No emojis. No bullet points. No numbered lists.\n"
    "3. Respond in the same language the user speaks to you.\n"
    "4. Keep responses concise and conversational, like a spoken dialogue.\n"
    "5. Only respond when directly addressed."
)

class Message(BaseModel):
    role: str
    content: str

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

    def chat(self, user_input: str) -> str:
        self.history.append(Message(role="user", content=user_input))
        messages = [msg.model_dump() for msg in self.history]

        try:
            print(f"🧠 Thinking...")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=1024
            )
            reply = response.choices[0].message.content
            self.history.append(Message(role="assistant", content=reply))
            return reply

        except APIConnectionError:
            return "Could not connect to the LLM server. Is LM Studio running and the server started?"
        except APITimeoutError:
            return "LLM request timed out. The model may still be loading."
        except APIError as e:
            return f"LLM Error: {e}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"

if __name__ == "__main__":
    brain = JarvisBrain()
    print(f"Jarvis Brain initialized | Provider: {os.getenv('LLM_PROVIDER')} | Model: {brain.model}")
    print("Type 'quit' to exit.")
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["quit", "exit", "bye"]:
            break
        print(f"Jarvis: {brain.chat(user_input)}")
