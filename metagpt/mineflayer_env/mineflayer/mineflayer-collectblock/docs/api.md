# API <!-- omit in toc -->

Welcome to the *mineflayer-collectblock* API documentation page.

## Table of Contents <!-- omit in toc -->

- [1. Summary](#1-summary)
- [Properties](#properties)
  - [`bot.collectblock.movements: Movements`](#botcollectblockmovements-movements)
- [Functions](#functions)
  - [collect](#collect)
    - [Options:](#options)

## 1. Summary

The collect block plugin is a utility plugin that can be used to help make collecting blocks and item drops very easy, using only a single API call. No need to worry about pathfinding to the block, selecting the right tool, or moving to pick up the item drop after mining.

## Properties

### `bot.collectblock.movements: Movements`

The movements object used by the pathfinder plugin to define the movement configuration. This object is passed to the pathfinder plugin when any API from this plugin is called in order to control how pathfinding should work when collecting the given blocks or item.

If set to null, the pathfinder plugin movements is not updated.

Defaults to a new movements object instance.

## Functions

### collect

Usage: `bot.collectblock.collect(target: Collectable | Collectable[], options?: CollectOptions, cb: (err?: Error) => void): void`

Causes the bot to collect the given block, item drop, or list of those. If the target is a block, the bot will move to the block, mine it, and pick up the item drop. If the target is an item drop, the bot will move to the item drop and pick it up. If the target is a list of collectables, the bot will move from target to target in order of closest to furthest and collect each target in turn.

#### Options:

  * `append: boolean`

    If true, the target(s) will be appended to the existing target list instead of starting a new task. Defaults to false.

  * `ignoreNoPath: boolean`

    If true, errors will not be thrown when a path to the target block cannot be found. The bot will attempt to choose the best available position it can find, instead. Errors are still thrown if the bot cannot interact with the block from it's final location. Defaults to false.

  * `chestLocations: Vec3[]`

    Gets the list of chest locations to use when storing items after the bot's inventory becomes full. If undefined, it defaults to the chest location list on the bot.collectBlock plugin.

  * `itemFilter: ItemFilter`

    When transferring items to a chest, this filter is used to determine what items are allowed to be moved, and what items aren't allowed to be moved. Defaults to the item filter specified on the bot.collectBlock plugin.