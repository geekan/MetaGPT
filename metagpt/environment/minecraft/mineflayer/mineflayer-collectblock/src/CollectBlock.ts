import { Bot } from "mineflayer";
import { Block } from "prismarine-block";
import { Movements, goals } from "mineflayer-pathfinder";
import { TemporarySubscriber } from "./TemporarySubscriber";
import { Entity } from "prismarine-entity";
import { error } from "./Util";
import { Vec3 } from "vec3";
import { emptyInventoryIfFull, ItemFilter } from "./Inventory";
import { findFromVein } from "./BlockVeins";
import { Collectable, Targets } from "./Targets";
import { Item } from "prismarine-item";
import mcDataLoader from "minecraft-data";
import { once } from "events";
import { callbackify } from "util";

export type Callback = (err?: Error) => void;

async function collectAll(
    bot: Bot,
    options: CollectOptionsFull
): Promise<void> {
    let success_count = 0;
    while (!options.targets.empty) {
        await emptyInventoryIfFull(
            bot,
            options.chestLocations,
            options.itemFilter
        );
        const closest = options.targets.getClosest();
        if (closest == null) break;
        switch (closest.constructor.name) {
            case "Block": {
                try {
                    if (success_count >= options.count) {
                        break;
                    }
                    await bot.tool.equipForBlock(
                        closest as Block,
                        equipToolOptions
                    );
                    const goal = new goals.GoalLookAtBlock(
                        closest.position,
                        bot.world
                    );
                    await bot.pathfinder.goto(goal);
                    await mineBlock(bot, closest as Block, options);
                    success_count++;
                    // TODO: options.ignoreNoPath
                } catch (err) {
                    // @ts-ignore
                    // console.log(err.stack)
                    // bot.pathfinder.stop()
                    // bot.waitForTicks(10)
                    try {
                        bot.pathfinder.setGoal(null);
                    } catch (err) {}
                    if (options.ignoreNoPath) {
                        // @ts-ignore
                        if (err.name === "Invalid block") {
                            console.log(
                                `Block ${closest.name} at ${closest.position} is not valid! Skip it!`
                            );
                        } // @ts-ignore
                        else if (err.name === "Unsafe block") {
                            console.log(
                                `${closest.name} at ${closest.position} is not safe to break! Skip it!`
                            );
                            // @ts-ignore
                        } else if (err.name === "NoItem") {
                            const properties =
                                bot.registry.blocksByName[closest.name];
                            const leastTool = Object.keys(
                                properties.harvestTools
                            )[0];
                            const item = bot.registry.items[leastTool];
                            bot.chat(
                                `I need at least a ${item.name} to mine ${closest.name}!  Skip it!`
                            );
                            return;
                        } else if (
                            // @ts-ignore
                            err.name === "NoPath" ||
                            // @ts-ignore
                            err.name === "Timeout"
                        ) {
                            if (
                                bot.entity.position.distanceTo(
                                    closest.position
                                ) < 0.5
                            ) {
                                await mineBlock(bot, closest as Block, options);
                                break;
                            }
                            console.log(
                                `No path to ${closest.name} at ${closest.position}! Skip it!`
                            );
                            // @ts-ignore
                        } else if (err.message === "Digging aborted") {
                            console.log(`Digging aborted! Skip it!`);
                        } else {
                            // @ts-ignore
                            bot.chat(`Error: ${err.message}`);
                        }
                        break;
                    }
                    throw err;
                }
                break;
            }
            case "Entity": {
                // Don't collect any entities that are marked as 'invalid'
                if (!(closest as Entity).isValid) break;
                try {
                    const tempEvents = new TemporarySubscriber(bot);
                    const waitForPickup = new Promise<void>(
                        (resolve, reject) => {
                            const timeout = setTimeout(() => {
                                // After 10 seconds, reject the promise
                                clearTimeout(timeout);
                                tempEvents.cleanup();
                                reject(new Error("Failed to pickup item"));
                            }, 10000);
                            tempEvents.subscribeTo(
                                "entityGone",
                                (entity: Entity) => {
                                    if (entity === closest) {
                                        clearTimeout(timeout);
                                        tempEvents.cleanup();
                                        resolve();
                                    }
                                }
                            );
                        }
                    );
                    bot.pathfinder.setGoal(
                        new goals.GoalFollow(closest as Entity, 0)
                    );
                    // await bot.pathfinder.goto(new goals.GoalBlock(closest.position.x, closest.position.y, closest.position.z))
                    await waitForPickup;
                } catch (err) {
                    // @ts-ignore
                    console.log(err.stack);
                    try {
                        bot.pathfinder.setGoal(null);
                    } catch (err) {}
                    if (options.ignoreNoPath) {
                        // @ts-ignore
                        if (err.message === "Failed to pickup item") {
                            bot.chat(`Failed to pickup item! Skip it!`);
                        }
                        break;
                    }
                    throw err;
                }
                break;
            }
            default: {
                throw error(
                    "UnknownType",
                    `Target ${closest.constructor.name} is not a Block or Entity!`
                );
            }
        }
        options.targets.removeTarget(closest);
    }
    bot.chat(`Collect finish!`);
}

const equipToolOptions = {
    requireHarvest: true,
    getFromChest: false,
    maxTools: 2,
};

async function mineBlock(
    bot: Bot,
    block: Block,
    options: CollectOptionsFull
): Promise<void> {
    if (
        bot.blockAt(block.position)?.type !== block.type ||
        bot.blockAt(block.position)?.type === 0
    ) {
        options.targets.removeTarget(block);
        throw error("Invalid block", "Block is not valid!");
        // @ts-expect-error
    } else if (!bot.pathfinder.movements.safeToBreak(block)) {
        options.targets.removeTarget(block);
        throw error("Unsafe block", "Block is not safe to break!");
    }

    await bot.tool.equipForBlock(block, equipToolOptions);

    if (!block.canHarvest(bot.heldItem ? bot.heldItem.type : bot.heldItem)) {
        options.targets.removeTarget(block);
        throw error("NoItem", "Bot does not have a harvestable tool!");
    }

    const tempEvents = new TemporarySubscriber(bot);
    tempEvents.subscribeTo("itemDrop", (entity: Entity) => {
        if (
            entity.position.distanceTo(block.position.offset(0.5, 0.5, 0.5)) <=
            0.5
        ) {
            options.targets.appendTarget(entity);
        }
    });
    try {
        await bot.dig(block);
        // Waiting for items to drop
        await new Promise<void>((resolve) => {
            let remainingTicks = 10;
            tempEvents.subscribeTo("physicTick", () => {
                remainingTicks--;
                if (remainingTicks <= 0) {
                    tempEvents.cleanup();
                    resolve();
                }
            });
        });
    } finally {
        tempEvents.cleanup();
    }
}

/**
 * A set of options to apply when collecting the given targets.
 */
export interface CollectOptions {
    /**
     * If true, the target(s) will be appended to the existing target list instead of
     * starting a new task. Defaults to false.
     */
    append?: boolean;

    /**
     * If true, errors will not be thrown when a path to the target block cannot
     * be found. The bot will attempt to choose the best available position it
     * can find, instead. Errors are still thrown if the bot cannot interact with
     * the block from it's final location. Defaults to false.
     */
    ignoreNoPath?: boolean;

    /**
     * Gets the list of chest locations to use when storing items after the bot's
     * inventory becomes full. If undefined, it defaults to the chest location
     * list on the bot.collectBlock plugin.
     */
    chestLocations?: Vec3[];

    /**
     * When transferring items to a chest, this filter is used to determine what
     * items are allowed to be moved, and what items aren't allowed to be moved.
     * Defaults to the item filter specified on the bot.collectBlock plugin.
     */
    itemFilter?: ItemFilter;

    /**
     * The total number of items to collect
     */
    count?: number;
}

/**
 * A version of collect options where all values are assigned.
 */
interface CollectOptionsFull {
    append: boolean;
    ignoreNoPath: boolean;
    chestLocations: Vec3[];
    itemFilter: ItemFilter;
    targets: Targets;
    count: number;
}

/**
 * The collect block plugin.
 */
export class CollectBlock {
    /**
     * The bot.
     */
    private readonly bot: Bot;

    /**
     * The list of active targets being collected.
     */
    private readonly targets: Targets;

    /**
     * The movements configuration to be sent to the pathfinder plugin.
     */
    movements?: Movements;

    /**
     * A list of chest locations which the bot is allowed to empty their inventory into
     * if it becomes full while the bot is collecting resources.
     */
    chestLocations: Vec3[] = [];

    /**
     * When collecting items, this filter is used to determine what items should be placed
     * into a chest if the bot's inventory becomes full. By default, returns true for all
     * items except for tools, weapons, and armor.
     *
     * @param item - The item stack in the bot's inventory to check.
     *
     * @returns True if the item should be moved into the chest. False otherwise.
     */
    itemFilter: ItemFilter = (item: Item) => {
        if (item.name.includes("helmet")) return false;
        if (item.name.includes("chestplate")) return false;
        if (item.name.includes("leggings")) return false;
        if (item.name.includes("boots")) return false;
        if (item.name.includes("shield")) return false;
        if (item.name.includes("sword")) return false;
        if (item.name.includes("pickaxe")) return false;
        if (item.name.includes("axe")) return false;
        if (item.name.includes("shovel")) return false;
        if (item.name.includes("hoe")) return false;
        return true;
    };

    /**
     * Creates a new instance of the create block plugin.
     *
     * @param bot - The bot this plugin is acting on.
     */
    constructor(bot: Bot) {
        this.bot = bot;
        this.targets = new Targets(bot);
        // @ts-ignore
        this.movements = new Movements(bot, mcDataLoader(bot.version));
    }

    /**
     * If target is a block:
     * Causes the bot to break and collect the target block.
     *
     * If target is an item drop:
     * Causes the bot to collect the item drop.
     *
     * If target is an array containing items or blocks, preforms the correct action for
     * all targets in that array sorting dynamically by distance.
     *
     * @param target - The block(s) or item(s) to collect.
     * @param options - The set of options to use when handling these targets
     * @param cb - The callback that is called finished.
     */
    async collect(
        target: Collectable | Collectable[],
        options: CollectOptions | Callback = {},
        cb?: Callback
    ): Promise<void> {
        if (typeof options === "function") {
            cb = options;
            options = {};
        }
        // @ts-expect-error
        if (cb != null) return callbackify(this.collect)(target, options, cb);

        const optionsFull: CollectOptionsFull = {
            append: options.append ?? false,
            ignoreNoPath: options.ignoreNoPath ?? false,
            chestLocations: options.chestLocations ?? this.chestLocations,
            itemFilter: options.itemFilter ?? this.itemFilter,
            targets: this.targets,
            count: options.count ?? Infinity,
        };

        if (this.bot.pathfinder == null) {
            throw error(
                "UnresolvedDependency",
                "The mineflayer-collectblock plugin relies on the mineflayer-pathfinder plugin to run!"
            );
        }

        if (this.bot.tool == null) {
            throw error(
                "UnresolvedDependency",
                "The mineflayer-collectblock plugin relies on the mineflayer-tool plugin to run!"
            );
        }

        if (this.movements != null) {
            this.bot.pathfinder.setMovements(this.movements);
        }

        if (!optionsFull.append) await this.cancelTask();
        if (Array.isArray(target)) {
            this.targets.appendTargets(target);
        } else {
            this.targets.appendTarget(target);
        }

        try {
            await collectAll(this.bot, optionsFull);
            this.targets.clear();
        } catch (err) {
            this.targets.clear();
            // Ignore path stopped error for cancelTask to work properly (imo we shouldn't throw any pathing errors)
            // @ts-expect-error
            if (err.name !== "PathStopped") throw err;
        } finally {
            // @ts-expect-error
            this.bot.emit("collectBlock_finished");
        }
    }

    /**
     * Loads all touching blocks of the same type to the given block and returns them as an array.
     * This effectively acts as a flood fill algorithm to retrieve blocks in the same ore vein and similar.
     *
     * @param block - The starting block.
     * @param maxBlocks - The maximum number of blocks to look for before stopping.
     * @param maxDistance - The max distance from the starting block to look.
     * @param floodRadius - The max distance distance from block A to block B to be considered "touching"
     */
    findFromVein(
        block: Block,
        maxBlocks = 100,
        maxDistance = 16,
        floodRadius = 1
    ): Block[] {
        return findFromVein(
            this.bot,
            block,
            maxBlocks,
            maxDistance,
            floodRadius
        );
    }

    /**
     * Cancels the current collection task, if still active.
     *
     * @param cb - The callback to use when the task is stopped.
     */
    async cancelTask(cb?: Callback): Promise<void> {
        if (this.targets.empty) {
            if (cb != null) cb();
            return await Promise.resolve();
        }
        this.bot.pathfinder.stop();
        if (cb != null) {
            // @ts-expect-error
            this.bot.once("collectBlock_finished", cb);
        }
        await once(this.bot, "collectBlock_finished");
    }
}
