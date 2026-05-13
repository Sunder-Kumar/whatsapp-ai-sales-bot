import os
from groq import AsyncGroq
from dotenv import load_dotenv
from typing import List, Dict

load_dotenv()

class GroqAI:
    def __init__(self, api_key: str = None, model: str = "llama-3.3-70b-versatile"):
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self.model = model
        self.client = None

        if not self.api_key:
            print("WARNING: GROQ_API_KEY not found in environment.")

    def _get_client(self):
        if self.client is None:
            self.client = AsyncGroq(api_key=self.api_key)
        return self.client

    async def generate_reply(self, messages: List[Dict[str, str]], temperature: float = 0.7) -> str:
        """
        Generates a reply using the Groq API.
        messages format: [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}]
        """
        client = self._get_client()
        try:
            response = await client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=300,
                temperature=temperature
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Groq API Error: {e}")
            return "Sorry, I'm having trouble thinking right now. Please try again in a moment."

# Global instance
ai_engine = GroqAI()
