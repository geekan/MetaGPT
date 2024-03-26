/**
 * Creates a new error object with the given type and message.
 *
 * @param type - The error type.
 * @param message - The error message.
 *
 * @returns The error object.
 */
export function error (type: string, message: string): Error {
  const e = new Error(message)
  e.name = type
  return e
}
