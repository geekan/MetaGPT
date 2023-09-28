import asyncio

from metagpt.minecraft_team import GameEnvironment
from metagpt.roles.minecraft.action_developer import ActionDeveloper
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

    code = """
    async function collectBamboo(bot) {
    // Equip the iron sword
    const ironSword = bot.inventory.findInventoryItem(mcData.itemsByName.iron_sword.id);
    await bot.equip(ironSword, "hand");

    // Find bamboo plants using the exploreUntil function
    const bambooPlants = await exploreUntil(bot, new Vec3(1, 0, 1), 60, () => {
        const bambooPlants = bot.findBlocks({
        matching: block => block.name === "bamboo",
        maxDistance: 32,
        count: 10
        });
        return bambooPlants.length >= 10 ? bambooPlants : null;
    });
    if (!bambooPlants) {
        bot.chat("Could not find enough bamboo plants.");
        return;
    }

    // Break 10 bamboo plants using the iron sword
    for (const bambooPlant of bambooPlants) {
        const block = bot.blockAt(bambooPlant);
        await bot.dig(block);
    }
    bot.chat("Broke 10 bamboo plants.");

    // Collect the dropped bamboo items
    for (const bambooPlant of bambooPlants) {
        await bot.pathfinder.goto(new GoalBlock(bambooPlant.x, bambooPlant.y, bambooPlant.z));
    }
    bot.chat("Collected 10 bamboo.");
    }
    """
    ad = ActionDeveloper()
    ge = GameEnvironment()
    ge.update_event(events)
    ad.set_memory(shared_memory=ge)
    msg = ad.encapsule_message(events=ge.event, code=code)
    logger.info(f"Encapsuled_message: {msg}")

    parsed_result = await ad.generate_action_code(**msg)

    logger.info(f"Parsed_code_updating: {parsed_result}")


if __name__ == "__main__":
    asyncio.run(main())
