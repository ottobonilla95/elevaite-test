"use client";

import { ColorContext, EngineerTheme } from "@elevaite/ui";

export function Providers({ children }) {
  return <ColorContext.Provider value={EngineerTheme}>{children}</ColorContext.Provider>;
}
