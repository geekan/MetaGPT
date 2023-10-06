# -*- coding: utf-8 -*-
# @Date    : 2023/09/28 00:08
# @Author  : yuymf
# @Desc    : 
from metagpt.utils.minecraft import parse_js_code, parse_action_response
from metagpt.logs import logger
from typing import Any


if __name__ == "__main__":
    msg = '''
    Explain: The code from the last round is a function called `collectBamboo` that is supposed to collect bamboo plants. It equips an iron sword, finds bamboo plants using the `exploreUntil` function, breaks 10 bamboo plants using the iron sword, and then collects the dropped bamboo items.

    Plan:
    1) Check if the bot has an iron sword in its inventory. If not, collect the necessary materials and craft an iron sword using the `craftItem` function.
    2) Use the `exploreUntil` function to find at least 10 bamboo plants. If the function times out or cannot find enough bamboo plants, return and chat "Could not find enough bamboo plants."
    3) Equip the iron sword.
    4) Iterate over the found bamboo plants and break them using the iron sword.
    5) Chat "Broke 10 bamboo plants."
    6) Iterate over the found bamboo plants and collect the dropped bamboo items.
    7) Chat "Collected 10 bamboo."

    Code:
    ```javascript
    async function collectBamboo(bot) {
        // Check if the bot has an iron sword
        const ironSword = bot.inventory.findInventoryItem(mcData.itemsByName.iron_sword.id);
        if (!ironSword) {
            // Collect the necessary materials to craft an iron sword
            await mineBlock(bot, "iron_ore", 3);
            await smeltItem(bot, "iron_ore", "oak_planks", 3);
            await craftItem(bot, "iron_sword", 1);
        }

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

        // Equip the iron sword
        await bot.equip(ironSword, "hand");

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
    ```
    '''

    logger.info(f"Parse_js_code result is HERE: {parse_js_code(msg)}")
    logger.info(f"Parse_action_response result is HERE: {parse_action_response(msg)}")