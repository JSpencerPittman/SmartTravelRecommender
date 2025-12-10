import os
from pathlib import Path
from typing import Literal, Optional

from chat.utility.message import Message  # type: ignore
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

ENV_VAR__API_KEY = "OPENAI_API_KEY"
SYSTEM_PROMPT_PATH = Path(__file__).parent / "prompt.txt"


def _read_system_prompt() -> str:
    with open(SYSTEM_PROMPT_PATH, "r") as infile:
        return "\n".join(infile.readlines())


def _create_chatbot_message(
    role: Literal["user", "assistant", "developer"], content: str
) -> dict[str, str]:
    return {"role": role, "content": content}


class Chatbot:
    def __init__(
        self, model: str = "gpt-5", temperature: float = 0.7, top_p: float = 0.99
    ):
        self._model: str = model
        self._temperature: float = temperature
        self._top_p: float = top_p
        self._client: Optional[OpenAI] = None

    def initialize_session(self) -> bool:
        api_key = os.environ.get(ENV_VAR__API_KEY)
        if api_key is None:
            return False
        try:
            self._client = OpenAI(api_key=api_key)
            return True
        except Exception:
            return False

    def prompt_completion(self, history: list[Message]) -> Optional[str]:
        assert self._client is not None

        messages = [_create_chatbot_message("developer", _read_system_prompt())]
        for msg in history:
            messages.append(
                _create_chatbot_message(
                    "user" if msg.is_user else "assistant", msg.message
                )
            )

        completion = self._client.chat.completions.create(
            messages=messages,  # type: ignore
            model=self._model,
        )

        return completion.choices[0].message.content
