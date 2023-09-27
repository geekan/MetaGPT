async function placeItem(bot, name, position) {
    // return if name is not string
    if (typeof name !== "string") {
        throw new Error(`name for placeItem must be a string`);
    }
    // return if position is not Vec3
    if (!(position instanceof Vec3)) {
        throw new Error(`position for placeItem must be a Vec3`);
    }
    const itemByName = mcData.itemsByName[name];
    if (!itemByName) {
        throw new Error(`No item named ${name}`);
    }
    const item = bot.inventory.findInventoryItem(itemByName.id);
    if (!item) {
        bot.chat(`No ${name} in inventory`);
        return;
    }
    const item_count = item.count;
    // find a reference block
    const faceVectors = [
        new Vec3(0, 1, 0),
        new Vec3(0, -1, 0),
        new Vec3(1, 0, 0),
        new Vec3(-1, 0, 0),
        new Vec3(0, 0, 1),
        new Vec3(0, 0, -1),
    ];
    let referenceBlock = null;
    let faceVector = null;
    for (const vector of faceVectors) {
        const block = bot.blockAt(position.minus(vector));
        if (block?.name !== "air") {
            referenceBlock = block;
            faceVector = vector;
            bot.chat(`Placing ${name} on ${block.name} at ${block.position}`);
            break;
        }
    }
    if (!referenceBlock) {
        bot.chat(
            `No block to place ${name} on. You cannot place a floating block.`
        );
        _placeItemFailCount++;
        if (_placeItemFailCount > 10) {
            throw new Error(
                `placeItem failed too many times. You cannot place a floating block.`
            );
        }
        return;
    }

    // You must use try catch to placeBlock
    try {
        // You must first go to the block position you want to place
        await bot.pathfinder.goto(new GoalPlaceBlock(position, bot.world, {}));
        // You must equip the item right before calling placeBlock
        await bot.equip(item, "hand");
        await bot.placeBlock(referenceBlock, faceVector);
        bot.chat(`Placed ${name}`);
        bot.save(`${name}_placed`);
    } catch (err) {
        const item = bot.inventory.findInventoryItem(itemByName.id);
        if (item?.count === item_count) {
            bot.chat(
                `Error placing ${name}: ${err.message}, please find another position to place`
            );
            _placeItemFailCount++;
            if (_placeItemFailCount > 10) {
                throw new Error(
                    `placeItem failed too many times, please find another position to place.`
                );
            }
        } else {
            bot.chat(`Placed ${name}`);
            bot.save(`${name}_placed`);
        }
    }
}
