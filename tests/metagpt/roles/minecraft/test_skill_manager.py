import asyncio

from metagpt.minecraft_team import GameEnvironment
from metagpt.roles.minecraft.skill_manager import SkillManager
from metagpt.logs import logger
from metagpt.actions.minecraft.manage_skills import (
    GenerateSkillDescription,
    RetrieveSkills,
    AddNewSkills,
)


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
    program_code = 'async function obtainSpruceLogs(bot) {\n  // Find 3 spruce_log blocks\n  const spruceLogs = await exploreUntil(bot, new Vec3(1, 0, 1), 60, () => {\n    const spruceLog = bot.findBlock({\n      matching: mcData.blocksByName["spruce_log"].id,\n      maxDistance: 32,\n      count: 3\n    });\n    return spruceLog ? spruceLog : null;\n  });\n  if (spruceLogs) {\n    // Mine the spruce_log blocks\n    await mineBlock(bot, "spruce_log", 3);\n    bot.chat("3 spruce logs obtained.");\n  } else {\n    bot.chat("Could not find enough spruce logs.");\n  }\n}'
    program_name = "obtainSpruceLogs"
    task = "Obtain 3 more spruce logs"
    skills = {
        "mineWoodLog": {
            "code": 'async function mineWoodLog(bot) {\n  const woodLogNames = ["oak_log", "birch_log", "spruce_log", "jungle_log", "acacia_log", "dark_oak_log", "mangrove_log"];\n\n  // Find a wood log block\n  const woodLog = await exploreUntil(bot, new Vec3(1, 0, 1), 60, () => {\n    for (const name of woodLogNames) {\n      const log = bot.findBlock({\n        matching: mcData.blocksByName[name].id,\n        maxDistance: 32\n      });\n      if (log) {\n        return log;\n      }\n    }\n    return null;\n  });\n  if (woodLog) {\n    // Mine the wood log block\n    await mineBlock(bot, woodLog.name, 1);\n    bot.chat("Wood log mined.");\n  } else {\n    bot.chat("Could not find a wood log.");\n  }\n}',
            "description": "async function mineWoodLog(bot) {\n    // The function is about mining a wood log block. It searches for a wood log block by exploring the environment until it finds one of the seven types of wood logs. Once a wood log block is found, it is mined and a message is sent to the chat. If a wood log block is not found, a message is sent to the chat indicating that it could not be found.\n}",
        },
        "obtainSpruceLogs": {
            "code": 'async function obtainSpruceLogs(bot) {\n  // Find 3 spruce_log blocks\n  const spruceLogs = await exploreUntil(bot, new Vec3(1, 0, 1), 60, () => {\n    const spruceLog = bot.findBlock({\n      matching: mcData.blocksByName["spruce_log"].id,\n      maxDistance: 32,\n      count: 3\n    });\n    return spruceLog ? spruceLog : null;\n  });\n  if (spruceLogs) {\n    // Mine the spruce_log blocks\n    await mineBlock(bot, "spruce_log", 3);\n    bot.chat("3 spruce logs obtained.");\n  } else {\n    bot.chat("Could not find enough spruce logs.");\n  }\n}',
            "description": "async function obtainSpruceLogs(bot) {\n    // The function is about obtaining 3 spruce logs. It explores the environment until it finds 3 spruce_log blocks within a certain distance. Once the blocks are found, it mines them and sends a message indicating that 3 spruce logs have been obtained. If the blocks are not found, it sends a message indicating that it could not find enough spruce logs.\n}",
        },
    }
    context = "Question: How to obtain 3 more spruce logs in Minecraft?\nAnswer: You can obtain more spruce logs in Minecraft by finding and chopping down spruce trees in a spruce forest biome. If you have already chopped down all the spruce trees in the area, you can either explore further to find more spruce trees or plant saplings and wait for them to grow into trees."

    sm = SkillManager()
    ge = GameEnvironment()
    ge.update_event(events)
    sm.set_memory(shared_memory=ge)

    generate_skill_message = sm.encapsule_message(program_code, program_name)
    logger.info(f"Generate_skill_message: {generate_skill_message}")
    desp = await sm.generate_skill_descp(**generate_skill_message)
    logger.info(f"Generate_skill_descp UPDATING: {desp}")

    add_new_skills_message = {
        "task": task,
        "program_name": program_name,
        "program_code": program_code,
        "skills": skills,
    }
    logger.info(f"Handle_add_new_skills_message: {add_new_skills_message}")
    new_skills_info = await sm.handle_add_new_skills(**add_new_skills_message)
    logger.info(f"Handle_add_new_skills UPDATING: {new_skills_info}")

    retrieve_skills_message_step1 = {"query": context}

    logger.info(f"Retrieve_skills_message: {retrieve_skills_message_step1}")
    skills = await sm.retrieve_skills(**retrieve_skills_message_step1)
    logger.info(f"Retrieve_skills UPDATING: {skills}")


if __name__ == "__main__":
    asyncio.run(main())
