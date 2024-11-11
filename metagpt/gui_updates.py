from metagpt.logs import logger

def update_gui_with_thinking_details(info):
    """Update GUI with thinking stage details"""
    try:
        # Extract details from the update_info
        state = info.get("state")
        actions = info.get("actions", [])
        current_action = info.get("current_action")
        history = info.get("history", [])
        important_memory = info.get("important_memory", [])

        # Log the information
        logger.debug("Thinking Update:")
        logger.debug(f"State: {state}")
        logger.debug(f"Available Actions: {actions}")
        logger.debug(f"Current Action: {current_action}")
        logger.debug(f"History Items: {len(history)}")
        logger.debug(f"Important Memory Items: {len(important_memory)}")
    except Exception as e:
        logger.error(f"Error updating thinking details: {e}")

def update_gui_with_acting_details(info):
    """Update GUI with acting stage details"""
    try:
        # Extract details from the update_info
        action = info.get("action")
        description = info.get("description")
        action_details = info.get("action_details", {})

        # Log the information
        logger.debug("Acting Update:")
        logger.debug(f"Action: {action}")
        logger.debug(f"Description: {description}")
        logger.debug(f"Details: {action_details}")
    except Exception as e:
        logger.error(f"Error updating acting details: {e}")

def update_gui_with_planning_details(info):
    """Update GUI with planning stage details"""
    try:
        # Extract details from the update_info
        current_task = info.get("current_task")
        task_description = info.get("task_description")
        plan = info.get("plan", {})

        # Log the information
        logger.debug("Planning Update:")
        logger.debug(f"Current Task: {current_task}")
        logger.debug(f"Description: {task_description}")
        logger.debug(f"Plan Details: {plan}")
    except Exception as e:
        logger.error(f"Error updating planning details: {e}")
