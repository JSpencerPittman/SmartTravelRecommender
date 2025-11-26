"""Implements the smart travel advisor chatbot."""

from collections.abc import Iterable
import os
from typing import Final

from dotenv import load_dotenv
from openai import OpenAI

from chat.utility.message import Message

load_dotenv()


class TravelChatbot:
    SYSTEM_PROMPT: Final[int] = """
    You must act as a highly knowledgeable and friendly travel guide who guides the user in determining where they would like to travel.
    In doing so, you should determine the user's preferences and make it easy for them to reveal their preferences by making conversation easy.
    Ultimately, you must recommend a few good travel destinations based on the user's preferences.
    Then, when the user selects a travel destination, recommend generating a travel itinerary and a budget, and do so upon user request.
    When asked, your name is simply Smart Travel Advisor.
    """

    def __init__(self, model: str = "gpt-5", temperature: float = 0.7, top_p: float = 0.99) -> None:
        self._client: OpenAI = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        self._model: str = model
        self._temperature: float = temperature
        self._top_p: float = top_p

    def generate_response(self, messages: Iterable[Message]) -> str:
        return self._client.responses.create(
            model=self._model,
            temperature=self._temperature,
            top_p=self._top_p,
            tools=[{"type": "web_search"}],
            instructions=self.SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user" if message.is_user else "assistant",
                    "content": message.message,
                }
                for message in messages
            ],
        ).output_text
