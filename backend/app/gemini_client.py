import asyncio
import os
from functools import cached_property

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()


class GeminiClient:
    def __init__(self):
        self.model = os.getenv(
            "GEMINI_MODEL",
            "gemma-4-26b-a4b-it",
        )

        self.thinking_level = os.getenv(
            "GEMINI_THINKING_LEVEL",
            "high",
        )

    @cached_property
    def client(self):
        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise RuntimeError(
                "GEMINI_API_KEY is missing. "
                "Set it in backend/.env to use AI features."
            )

        return genai.Client(api_key=api_key)

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> str:
        def request():
            response = self.client.models.generate_content(
                model=self.model,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=0.2,
                    thinking_config=types.ThinkingConfig(
                        thinking_level=self.thinking_level,
                    ),
                ),
            )

            if not response.text:
                raise RuntimeError(
                    "Gemini returned an empty response."
                )

            return response.text

        try:
            return await asyncio.to_thread(request)
        except RuntimeError:
            raise
        except Exception as exc:
            # Avoid exposing API keys or raw request details to users.
            raise RuntimeError(
                f"Gemini request failed ({type(exc).__name__}). "
                "Check the API key, model availability, quota, "
                "and network connection."
            ) from exc


gemini_client = GeminiClient()