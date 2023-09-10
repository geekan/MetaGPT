"""
This module contains the default callback handler.
"""
from typing import Optional
from metagpt.callbacks.base_callback_handler import BaseCallbackHandler, SenderInfo

class StdoutCallbackHander(BaseCallbackHandler):
    """
    Default callback handler that prints the message to stdout.
    """

    def on_new_message(self, sender_info:Optional[SenderInfo])->None:
        """
        Called when a new message is received.
        Args:
            sender_info: Sender Info object containing sender info
        """
        if sender_info is None:
            print("System says:")
        else:
            print(f"{sender_info.name} ({sender_info.role}) says:")


    def on_new_token_generated(self, token: str) -> None:
        print(token, end="")

    def on_message_end(self) -> None:
        print()