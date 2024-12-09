from typing import Optional, Dict, Any
import asyncio
from metagpt.logs import logger

class WebSocketClient:
    _callback = None

    @classmethod
    def set_callback(cls, callback):
        cls._callback = callback

    @classmethod
    async def send_update(cls, update_info: Dict[str, Any]):
        if cls._callback:
            try:
                if asyncio.iscoroutinefunction(cls._callback):
                    await cls._callback(update_info)
                else:
                    cls._callback(update_info)
            except Exception as e:
                logger.error(f"Error sending WebSocket update: {e}")
        else:
            logger.warning("No WebSocket callback set")
