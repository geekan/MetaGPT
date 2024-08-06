import type { Callback } from './index'
export type Task = (cb: Callback) => void
export type SyncTask = () => void

/**
 * A simple utility class for queuing up a series of async tasks to execute.
 */
export class TaskQueue {
  private tasks: Task[] = []

  /**
   * If true, the task list will stop executing if one of the tasks throws an error.
   */
  readonly stopOnError: boolean = true

  /**
   * Adds a new async task to this queue. The provided callback should be executed when
   * the async task is complete.
   *
   * @param task - The async task to add.
   */
  add (task: Task): void {
    this.tasks.push(task)
  }

  /**
   * Adds a synchronous task toi this queue.
   *
   * @param task - The sync task to add.
   */
  addSync (task: SyncTask): void {
    this.add((cb) => {
      try {
        task()
        cb()
      } catch (err: any) {
        cb(err)
      }
    })
  }

  /**
   * Runs all tasks currently in this queue and empties the queue.
   *
   * @param cb - The optional callback to be executed when all tasks in this queue have
   * finished executing.
   */
  runAll (cb?: Callback): void {
    const taskList = this.tasks
    this.tasks = []

    let index = -1
    const runNext: () => void = () => {
      index++
      if (index >= taskList.length) {
        if (cb !== undefined) cb()
        return
      }

      try {
        taskList[index]((err) => {
          if (err !== undefined) {
            if (cb !== undefined) cb(err)

            if (this.stopOnError) return
          }

          runNext()
        })
      } catch (err: any) {
        if (cb !== undefined) cb(err)
      }
    }

    runNext()
  }
}
