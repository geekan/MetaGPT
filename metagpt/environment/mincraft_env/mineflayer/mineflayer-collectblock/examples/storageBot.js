/**
 * This bot example shows how to use the chest filling mechanic of the plugin.
 * Simply provide a given storage chest, and the bot will automatically try and
 * store it's inventory in that chest when the bot's inventory becomes full.
 */

if (process.argv.length < 4 || process.argv.length > 6) {
  console.log('Usage : node storageBot.js <host> <port> [<name>] [<password>]')
  process.exit(1)
}

// Load your libraries
const mineflayer = require('mineflayer')
const collectBlock = require('mineflayer-collectblock').plugin

// Create your bot
const bot = mineflayer.createBot({
  host: process.argv[2],
  port: parseInt(process.argv[3]),
  username: process.argv[4] ? process.argv[4] : 'storageBot',
  password: process.argv[5]
})

// Load the collect block plugin
bot.loadPlugin(collectBlock)

// Load mcData on login
let mcData
bot.once('login', () => {
  mcData = require('minecraft-data')(bot.version)
})

// On spawn, try to find any nearby chests and save those as storage locations.
// When the bot's inventory becomes too full, it will empty it's inventory into
// these chests before collecting more resources. If a chest gets full, it moves
// to the next one in order until it's inventory is empty or it runs out of chests.
bot.once('spawn', () => {
  bot.collectBlock.chestLocations = bot.findBlocks({
    matching: mcData.blocksByName.chest.id,
    maxDistance: 16,
    count: 999999 // Get as many chests as we can
  })

  if (bot.collectBlock.chestLocations.length === 0) {
    bot.chat("I don't see any chests nearby.")
  } else {
    for (const chestPos of bot.collectBlock.chestLocations) {
      bot.chat(`I found a chest at ${chestPos}`)
    }
  }
})

// Wait for someone to say something
bot.on('chat', async (username, message) => {
  // If the player says something start starts with "collect"
  // Otherwise, do nothing
  const args = message.split(' ')
  if (args[0] !== 'collect') return

  // If the player specifies a number, collect that many. Otherwise, default to 1.
  let count = 1
  if (args.length === 3) count = parseInt(args[1])

  // If a number was given the item number is the 3rd arg, not the 2nd.
  let type = args[1]
  if (args.length === 3) type = args[2]

  // Get the id of that block type for this version of Minecraft.
  const blockType = mcData.blocksByName[type]
  if (!blockType) {
    bot.chat(`I don't know any blocks named ${type}.`)
    return
  }

  // Find all nearby blocks of that type, up to the given count, within 64 blocks.
  const blocks = bot.findBlocks({
    matching: blockType.id,
    maxDistance: 64,
    count: count
  })

  // Complain if we can't find any nearby blocks of that type.
  if (blocks.length === 0) {
    bot.chat("I don't see that block nearby.")
    return
  }

  // Convert the block position array into a block array to pass to collect block.
  const targets = []
  for (let i = 0; i < Math.min(blocks.length, count); i++) {
    targets.push(bot.blockAt(blocks[i]))
  }

  // Announce what we found.
  bot.chat(`Found ${targets.length} ${type}(s)`)

  // Tell the bot to collect all of the given blocks in the block list.
  try {
    await bot.collectBlock.collect(targets)
    // All blocks have been collected.
    bot.chat('Done')
  } catch (err) {
    // An error occurred, report it.
    bot.chat(err.message)
    console.log(err)
  }
})
