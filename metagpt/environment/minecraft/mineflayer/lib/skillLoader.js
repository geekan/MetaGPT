function inject(bot) {
    bot._sleep = bot.sleep;
    bot.sleep = async (bedBlock) => {
        await bot.waitForTicks(20);
        await bot._sleep(bedBlock);
        await bot.waitForTicks(135);
    };

    bot._fish = bot.fish;
    bot.fish = async () => {
        if (bot.heldItem?.name !== "fishing_rod") {
            bot.chat("I'm not holding a fishing rod!");
            return;
        }
        let timeout = null;
        await Promise.race([
            bot._fish(),
            new Promise(
                (resolve, reject) =>
                    (timeout = setTimeout(() => {
                        bot.activateItem();
                        reject(
                            new Error(
                                "Finishing timeout, make sure you get to and look at a water block!"
                            )
                        );
                    }, 60000))
            ),
        ]);
        clearTimeout(timeout);
        await bot.waitForTicks(20);
    };

    bot._consume = bot.consume;
    bot.consume = async () => {
        // action_count.activateItem++;
        await bot._consume();
        await bot.waitForTicks(20);
    };

    bot._useOn = bot.useOn;
    bot.useOn = async (entity) => {
        if (entity.position.distanceTo(bot.entity.position) > 6) {
            bot.chat("Please goto a place near the entity first!");
            return;
        }
        await bot._useOn(entity);
        await bot.waitForTicks(20);
    };

    bot._activateBlock = bot.activateBlock;
    bot.activateBlock = async (block) => {
        if (block.position.distanceTo(bot.entity.position) > 6) {
            bot.chat("Please goto a place near the block first!");
            return;
        }
        // action_count.activateBlock++;
        await bot._activateBlock(block);
    };

    bot._chat = bot.chat;
    bot.chat = (message) => {
        // action_count.chat++;
        bot.emit("chatEvent", "bot", message);
        bot._chat(message);
    };

    bot.inventoryUsed = () => {
        return bot.inventory.slots.slice(9, 45).filter((item) => item !== null)
            .length;
    };

    bot.save = function (eventName) {
        bot.emit("save", eventName);
    };
}

// export all control_primitives
module.exports = { inject };
