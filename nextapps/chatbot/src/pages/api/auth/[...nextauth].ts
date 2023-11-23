import NextAuth, { NextAuthOptions } from "next-auth"
import CredentialsProvider from 'next-auth/providers/credentials';
import Providers from 'next-auth/providers';
import GoogleProvider from "next-auth/providers/google";


export const authOptions: NextAuthOptions = {
    // https://next-auth.js.org/configuration/providers/oauth
    providers: [
    ],
    callbacks: {
      async jwt({ token, user }) {
        return {...token, ...user};
      },
      async session({session, token, user}){
        session.user = token;
        return session;
      }
    },
  }
  
  export default NextAuth(authOptions)