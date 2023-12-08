import "@/styles/globals.css";
import type { AppProps } from "next/app";
import { SessionProvider, getSession } from "next-auth/react";
import { ReactNode } from "react";
import { headers } from "next/headers";
interface Props {
  children: ReactNode;
}

export default function App({ Component, pageProps: { session, ...pageProps } }: AppProps) {
  return (
    <SessionProvider session={session}>
      <Component {...pageProps} />
    </SessionProvider>
  );
}
