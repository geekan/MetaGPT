async function killMob(bot, mobName, timeout = 300) {
    // return if mobName is not string
    if (typeof mobName !== "string") {
        throw new Error(`mobName for killMob must be a string`);
    }
    // return if timeout is not number
    if (typeof timeout !== "number") {
        throw new Error(`timeout for killMob must be a number`);
    }

    const weaponsForShooting = [
        "bow",
        "crossbow",
        "snowball",
        "ender_pearl",
        "egg",
        "splash_potion",
        "trident",
    ];
    const mainHandItem = bot.inventory.slots[bot.getEquipmentDestSlot("hand")];

    const entity = bot.nearestEntity(
        (entity) =>
            entity.name === mobName &&
            // kill mob distance should be slightly bigger than explore distance
            entity.position.distanceTo(bot.entity.position) < 48
    );
    if (!entity) {
        bot.chat(`No ${mobName} nearby, please explore first`);
        _killMobFailCount++;
        if (_killMobFailCount > 10) {
            throw new Error(
                `killMob failed too many times, make sure you explore before calling killMob`
            );
        }
        return;
    }

    let droppedItem;
    if (mainHandItem && weaponsForShooting.includes(mainHandItem.name)) {
        bot.hawkEye.autoAttack(entity, mainHandItem.name);
        droppedItem = await waitForMobShot(bot, entity, timeout);
    } else {
        await bot.pvp.attack(entity);
        droppedItem = await waitForMobRemoved(bot, entity, timeout);
    }
    if (droppedItem) {
        await bot.collectBlock.collect(droppedItem, { ignoreNoPath: true });
    }
    bot.save(`${mobName}_killed`);
}
