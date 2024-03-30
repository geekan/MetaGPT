const Observation = require("./base.js").Observation;

class Status extends Observation {
    constructor(bot) {
        super(bot);
        this.name = "status";
    }

    observe() {
        return {
            health: this.bot.health,
            food: this.bot.food,
            saturation: this.bot.foodSaturation,
            oxygen: this.bot.oxygenLevel,
            position: this.bot.entity.position,
            velocity: this.bot.entity.velocity,
            yaw: this.bot.entity.yaw,
            pitch: this.bot.entity.pitch,
            onGround: this.bot.entity.onGround,
            equipment: this.getEquipment(),
            name: this.bot.entity.username,
            timeSinceOnGround: this.bot.entity.timeSinceOnGround,
            isInWater: this.bot.entity.isInWater,
            isInLava: this.bot.entity.isInLava,
            isInWeb: this.bot.entity.isInWeb,
            isCollidedHorizontally: this.bot.entity.isCollidedHorizontally,
            isCollidedVertically: this.bot.entity.isCollidedVertically,
            biome: this.bot.blockAt(this.bot.entity.position)
                ? this.bot.blockAt(this.bot.entity.position).biome.name
                : "None",
            entities: this.getEntities(),
            timeOfDay: this.getTime(),
            inventoryUsed: this.bot.inventoryUsed(),
            elapsedTime: this.bot.globalTickCounter,
        };
    }

    itemToObs(item) {
        if (!item) return null;
        return item.name;
    }

    getTime() {
        const timeOfDay = this.bot.time.timeOfDay;
        let time = "";
        if (timeOfDay < 1000) {
            time = "sunrise";
        } else if (timeOfDay < 6000) {
            time = "day";
        } else if (timeOfDay < 12000) {
            time = "noon";
        } else if (timeOfDay < 13000) {
            time = "sunset";
        } else if (timeOfDay < 18000) {
            time = "night";
        } else if (timeOfDay < 22000) {
            time = "midnight";
        } else {
            time = "sunrise";
        }
        return time;
    }

    // For each item in equipment, if it exists, return the name of the item
    // otherwise return null
    getEquipment() {
        const slots = this.bot.inventory.slots;
        const mainHand = this.bot.heldItem;
        return slots
            .slice(5, 9)
            .concat(mainHand, slots[45])
            .map(this.itemToObs);
    }

    getEntities() {
        const entities = this.bot.entities;
        if (!entities) return {};
        // keep all monsters in one list, keep other mobs in another list
        const mobs = {};
        for (const id in entities) {
            const entity = entities[id];
            if (!entity.displayName) continue;
            if (entity.name === "player" || entity.name === "item") continue;
            if (entity.position.distanceTo(this.bot.entity.position) < 32) {
                if (!mobs[entity.name]) {
                    mobs[entity.name] = entity.position.distanceTo(
                        this.bot.entity.position
                    );
                } else if (
                    mobs[entity.name] >
                    entity.position.distanceTo(this.bot.entity.position)
                ) {
                    mobs[entity.name] = entity.position.distanceTo(
                        this.bot.entity.position
                    );
                }
            }
        }
        return mobs;
    }
}

module.exports = Status;
