import { Bot } from 'mineflayer'
import { Callback } from './CollectBlock'
import { Vec3 } from 'vec3'
import { error } from './Util'
import { Item } from 'prismarine-item'
import { goals } from 'mineflayer-pathfinder'
import { callbackify } from 'util'

export type ItemFilter = (item: Item) => boolean

function getClosestChest (bot: Bot, chestLocations: Vec3[]): Vec3 | null {
  let chest = null
  let distance = 0

  for (const c of chestLocations) {
    const dist = c.distanceTo(bot.entity.position)
    if (chest == null || dist < distance) {
      chest = c
      distance = dist
    }
  }

  if (chest != null) {
    chestLocations.splice(chestLocations.indexOf(chest), 1)
  }

  return chest
}

export async function emptyInventoryIfFull (bot: Bot, chestLocations: Vec3[], itemFilter: ItemFilter, cb?: Callback): Promise<void> {
  // @ts-expect-error
  if (cb != null) return callbackify(emptyInventoryIfFull)(bot, chestLocations, cb)
  if (bot.inventory.emptySlotCount() > 0) return
  return await emptyInventory(bot, chestLocations, itemFilter)
}

export async function emptyInventory (bot: Bot, chestLocations: Vec3[], itemFilter: ItemFilter, cb?: Callback): Promise<void> {
  // @ts-expect-error
  if (cb != null) return callbackify(emptyInventory)(bot, chestLocations, cb)
  if (chestLocations.length === 0) {
    throw error('NoChests', 'There are no defined chest locations!')
  }

  // Shallow clone so we can safely remove chests from the list that are full.
  chestLocations = [...chestLocations]

  while (true) {
    const chest = getClosestChest(bot, chestLocations)
    if (chest == null) {
      throw error('NoChests', 'All chests are full.')
    }
    const hasRemaining = await tryEmptyInventory(bot, chest, itemFilter)
    if (!hasRemaining) return
  }
}

async function tryEmptyInventory (bot: Bot, chestLocation: Vec3, itemFilter: ItemFilter, cb?: (err: Error | undefined, hasRemaining: boolean) => void): Promise<boolean> {
  // @ts-expect-error
  if (cb != null) return callbackify(tryEmptyInventory)(bot, chestLocation, itemFilter, cb)
  await gotoChest(bot, chestLocation)
  return await placeItems(bot, chestLocation, itemFilter)
}

async function gotoChest (bot: Bot, location: Vec3, cb?: Callback): Promise<void> {
  // @ts-expect-error
  if (cb != null) return callbackify(gotoChest)(bot, location)
  await bot.pathfinder.goto(new goals.GoalGetToBlock(location.x, location.y, location.z))
}

async function placeItems (bot: Bot, chestPos: Vec3, itemFilter: ItemFilter, cb?: (err: Error | undefined, hasRemaining: boolean) => void): Promise<boolean> {
  // @ts-expect-error
  if (cb != null) return callbackify(placeItems)(bot, chestPos, itemFilter, cb)
  const chestBlock = bot.blockAt(chestPos)
  if (chestBlock == null) {
    throw error('UnloadedChunk', 'Chest is in an unloaded chunk!')
  }
  const chest = await bot.openChest(chestBlock)
  for (const item of bot.inventory.items()) {
    if (!itemFilter(item)) continue
    if (chest.firstEmptyContainerSlot() === null) {
      // We have items that didn't fit.
      return true
    }
    await chest.deposit(item.type, item.metadata, item.count)
  }
  return false
}
