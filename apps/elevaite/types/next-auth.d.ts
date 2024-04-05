/* eslint-disable unicorn/filename-case -- The filename is important */

// eslint-disable-next-line @typescript-eslint/no-unused-vars -- This is important
import NextAuth from 'next-auth'

declare module 'next-auth' {
  interface Session {
    authToken?: string
  }
}
