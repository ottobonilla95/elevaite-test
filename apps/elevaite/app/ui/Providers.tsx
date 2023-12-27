"use client";

import { SessionProvider } from "next-auth/react";
import type { ReactNode, JSX } from "react";

function Providers({ children }: { children?: ReactNode }): JSX.Element {
  return <SessionProvider>{children}</SessionProvider>;
}

export default Providers;
