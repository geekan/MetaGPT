from typing import Dict, Any
import asyncio
from metagpt.utils.websocket_client import WebSocketClient
from metagpt.gui_updates import update_gui_with_thinking_details, update_gui_with_acting_details, update_gui_with_planning_details
from metagpt.logs import logger

async def gui_update_callback(update_info: Dict[str, Any]):
    """Callback function to update the GUI based on the update_info."""
    try:
        # First send to WebSocket if available
        await WebSocketClient.send_update(update_info)
        
        # Then update local GUI components based on event type
        event_type = update_info.get('event')
        if event_type == 'thinking':
            update_gui_with_thinking_details(update_info)
        elif event_type == 'acting':
            update_gui_with_acting_details(update_info)
        elif event_type == 'planning_and_acting':
            update_gui_with_planning_details(update_info)
        elif event_type == 'team_progress':
            # Handle team progress updates
            logger.debug(f"Team progress update: Round {update_info.get('round')}")
            await WebSocketClient.send_update({
                "event": "team_progress",
                "round": update_info.get('round'),
                "messages": update_info.get('messages', [])
            })
    except Exception as e:
        logger.error(f"Error in GUI update callback: {e}")
