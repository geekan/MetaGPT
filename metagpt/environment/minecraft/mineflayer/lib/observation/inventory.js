const { Observation } = require("./base");

class Inventory extends Observation {
    constructor(bot) {
        super(bot);
        this.name = "inventory";
    }

    observe() {
        return listItems(this.bot);
    }
}

function listItems(bot) {
    const items = getInventoryItems(bot);
    return items.reduce(itemToDict, {});
}

function getInventoryItems(bot) {
    const inventory = bot.currentWindow || bot.inventory;
    return inventory.items();
}

function itemToDict(acc, cur) {
    if (cur.name && cur.count) {
        //if both name and count property are defined
        if (acc[cur.name]) {
            //if the item is already in the dict
            acc[cur.name] += cur.count;
        } else {
            //if the item is not in the dict
            acc[cur.name] = cur.count;
        }
    }
    return acc;
}

//export modules
module.exports = Inventory;
