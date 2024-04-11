// Blocks = require("./blocks")
const { Observation } = require("./base");

class Voxels extends Observation {
    constructor(bot) {
        super(bot);
        this.name = "voxels";
    }

    observe() {
        return Array.from(getSurroundingBlocks(this.bot, 8, 2, 8));
    }
}

class BlockRecords extends Observation {
    constructor(bot) {
        super(bot);
        this.name = "blockRecords";
        this.records = new Set();
        this.tick = 0;
        bot.on("physicsTick", () => {
            this.tick++;
            if (this.tick >= 100) {
                const items = getInventoryItems(this.bot);
                getSurroundingBlocks(this.bot, 8, 2, 8).forEach((block) => {
                    if (!items.has(block)) this.records.add(block);
                });
                this.tick = 0;
            }
        });
    }

    observe() {
        return Array.from(this.records);
    }

    reset() {
        this.records = new Set();
    }
}

function getSurroundingBlocks(bot, x_distance, y_distance, z_distance) {
    const surroundingBlocks = new Set();

    for (let x = -x_distance; x <= x_distance; x++) {
        for (let y = -y_distance; y <= y_distance; y++) {
            for (let z = -z_distance; z <= z_distance; z++) {
                const block = bot.blockAt(bot.entity.position.offset(x, y, z));
                if (block && block.type !== 0) {
                    surroundingBlocks.add(block.name);
                }
            }
        }
    }
    // console.log(surroundingBlocks);
    return surroundingBlocks;
}

function getInventoryItems(bot) {
    const items = new Set();
    bot.inventory.items().forEach((item) => {
        if (item) items.add(item.name);
    });
    return items;
}

module.exports = { Voxels, BlockRecords };
