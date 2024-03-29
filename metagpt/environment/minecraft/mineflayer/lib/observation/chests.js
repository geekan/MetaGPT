const { Observation } = require("./base");

class Chests extends Observation {
    constructor(bot) {
        super(bot);
        this.name = "nearbyChests";
        this.chestsItems = {};
        bot.on("closeChest", (chestItems, position) => {
            this.chestsItems[position] = chestItems;
        });
        bot.on("removeChest", (chestPosition) => {
            this.chestsItems[chestPosition] = "Invalid";
        });
    }

    observe() {
        const chests = this.bot.findBlocks({
            matching: this.bot.registry.blocksByName.chest.id,
            maxDistance: 16,
            count: 999,
        });
        chests.forEach((chest) => {
            if (!this.chestsItems.hasOwnProperty(chest)) {
                this.chestsItems[chest] = "Unknown";
            }
        });
        return this.chestsItems;
    }
}

module.exports = Chests;
