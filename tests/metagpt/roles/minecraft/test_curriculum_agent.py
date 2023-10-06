import asyncio

from metagpt.minecraft_team import GameEnvironment
from metagpt.roles.minecraft.curriculum_agent import CurriculumDesigner
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

    cd = CurriculumDesigner()
    ge = GameEnvironment()
    ge.update_event(events)
    cd.set_memory(shared_memory=ge)

    task_msg = cd.encapsule_design_task_message(
        events=ge.event, chest_observation=ge.chest_observation
    )
    logger.info(f"Encapsuled_design_task_message: {task_msg}")
    task = await cd.handle_task_design(**task_msg)
    logger.info(f"Design_task_updating: {task}")

    context_msg = cd.encapsule_design_curriculum_message(
        events=ge.event, chest_observation=ge.chest_observation
    )
    logger.info(f"Encapsuled_design_context_message: {context_msg}")
    context = await cd.handle_curriculum_design(**context_msg)
    logger.info(f"Design_context_updating: {context}")


if __name__ == "__main__":
    asyncio.run(main())
