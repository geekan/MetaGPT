import asyncio

from metagpt.minecraft_team import GameEnvironment
from metagpt.roles.minecraft.critic_agent import CriticReviewer
from metagpt.logs import logger


async def main():
    events = [
        [
            "observe",
            {
                "voxels": ["grass_block", "dirt", "grass"],
                "status": {
                    "health": 20,
                    "food": 20,
                    "saturation": 5,
                    "oxygen": 20,
                    "position": {"x": 0.5, "y": 84, "z": -207.5},
                    "velocity": {"x": 0, "y": -0.0784000015258789, "z": 0},
                    "yaw": 3.141592653589793,
                    "pitch": 0,
                    "onGround": True,
                    "equipment": [None, None, None, None, None, None],
                    "name": "bot",
                    "isInWater": False,
                    "isInLava": False,
                    "isCollidedHorizontally": False,
                    "isCollidedVertically": True,
                    "biome": "plains",
                    "entities": {
                        "chicken": 29.071822119730644,
                        "sheep": 20.361212992763768,
                    },
                    "timeOfDay": "day",
                    "inventoryUsed": 0,
                    "elapsedTime": 41,
                },
                "inventory": {},
                "nearbyChests": {"(1344, 64, 1381)": "Unknown"},
                "blockRecords": ["grass_block", "dirt", "grass"],
            },
        ]
    ]
    task = "Obtain 3 more spruce logs"
    chest_observation = "Chests: None\n\n"

    context = "Question: How to obtain 3 more spruce logs in Minecraft?\nAnswer: You can obtain more spruce logs in Minecraft by finding and chopping down spruce trees in a spruce forest biome. If you have already chopped down all the spruce trees in the area, you can either explore further to find more spruce trees or plant saplings and wait for them to grow into trees."
    cr = CriticReviewer()
    ge = GameEnvironment()
    ge.update_event(events)
    cr.set_memory(shared_memory=ge)
    msg = cr.encapsule_message(
        events=ge.event, task=task, context=context, chest_observation=chest_observation
    )
    logger.info(f"Encapsuled_message: {msg}")

    verify = await cr.verify_task(**msg)

    logger.info(f"Parsed_code_updating: {verify}")


if __name__ == "__main__":
    asyncio.run(main())
