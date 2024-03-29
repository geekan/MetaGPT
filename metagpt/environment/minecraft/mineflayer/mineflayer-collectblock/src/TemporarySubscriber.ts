import { Bot } from 'mineflayer'

class Subscription {
  constructor (readonly eventName: string, readonly callback: Function) {}
}

export class TemporarySubscriber {
  private readonly subscriptions: Subscription[] = []

  constructor (readonly bot: Bot) {}

  /**
   * Adds a new temporary event listener to the bot.
   *
   * @param event - The event to subscribe to.
   * @param callback - The function to execute.
   */
  subscribeTo (event: string, callback: Function): void {
    this.subscriptions.push(new Subscription(event, callback))

    // @ts-expect-error
    this.bot.on(event, callback)
  }

  /**
   * Removes all attached event listeners from the bot.
   */
  cleanup (): void {
    for (const sub of this.subscriptions) {
      // @ts-expect-error
      this.bot.removeListener(sub.eventName, sub.callback)
    }
  }
}
