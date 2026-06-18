import os
from typing import List
from openai import OpenAI
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()

class Message(BaseModel):
    role: str
    content: str

class JarvisBrain:
    def __init__(self, model: str = None):
        # Unified LLM Configuration
        provider = os.getenv("LLM_PROVIDER", "openai").lower()
        base_url = os.getenv("LLM_BASE_URL")
        api_key = os.getenv("LLM_API_KEY")
        model_name = model or os.getenv("LLM_MODEL") or "gpt-4o"

        if provider == "lmstudio":
            # LM Studio / Local provider
            self.client = OpenAI(
                base_url=base_url,
                api_key=api_key or "lm-studio"
            )
            self.model = model_name
        else:
            # Default to OpenAI
            # If LLM_BASE_URL is provided even for openai, use it (e.g. for proxy)
            self.client = OpenAI(
                base_url=base_url,
                api_key=os.getenv("OPENAI_API_KEY") or api_key
            )
            self.model = model_name

        self.history: List[Message] = []

    def chat(self, user_input: str) -> str:
        # Add user message to history
        self.history.append(Message(role="user", content=user_input))
        
        # Prepare messages for the API
        messages = [msg.model_dump() for msg in self.history]
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=1024
            )
            
            reply = response.choices[0].message.content
            
            # Add assistant response to history
            self.history.append(Message(role="assistant", content=reply))
            return reply
        
        except Exception as e:
            return f"Error communicating with the brain: {str(e)}"

if __name__ == "__main__":
    brain = JarvisBrain()
    print(f"Jarvis Brain initialized | Provider: {os.getenv('LLM_PROVIDER')} | Model: {brain.model}")
    print("Type 'quit' to exit.")
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["quit", "exit", "bye"]:
            break
        print(f"Jarvis: {brain.chat(user_input)}")
