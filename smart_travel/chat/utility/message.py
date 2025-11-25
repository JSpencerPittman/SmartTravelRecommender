from dataclasses import dataclass
from typing import Optional


@dataclass
class Message(object):
    message: str
    is_user: bool

    def serialize(self) -> str:
        """
        Serialize the message.

        Returns:
            str: Serialized message with the proper source label.
        """

        return f"### {'User' if self.is_user else 'Agent'}\n{self.message}\n"

    @classmethod
    def deserialize_messages(cls, raw_contents: list[str]) -> list["Message"]:
        """
        Deserialize a series of messages from the raw contents of a text file.

        Args:
            raw_contents (list[str]): lines of text file to be parsed.

        Returns:
            list[Message]: All parsed messages from the text file.
        """

        def parse_source_label(line: str) -> Optional[bool]:
            """
            A source label is a line above a message's contents indicating who is the source or
            of the message: user or agent.

            A source label must follow the following format:
            ### <User|Agent>

            Args:
                line (str): potential source label to be parsed.

            Returns:
                Optional[bool]: If the line is not a source label, return None. Otherwise,
                return a boolean indicating if the source is the user, if not then it's the
                agent.
            """

            if not line.startswith("### "):
                return None
            parts = line.split("### ")
            if len(parts) != 2 or len(parts[1]) == 0:
                return None
            return parts[1].strip().lower() == "user"

        line_iter = iter(raw_contents)
        messages = []
        is_user = False
        message = ""
        source_label_encountered = False

        while (line := next(line_iter, None)) is not None:
            if (next_is_user := parse_source_label(line)) is not None:
                if len(message) and source_label_encountered:
                    messages.append(Message(message, is_user))
                is_user = next_is_user
                message = ""
                source_label_encountered = True
            else:
                message += line
        # loop terminates before the adding the final message.
        if len(message) and source_label_encountered:
            messages.append(cls(message, is_user))

        return messages
