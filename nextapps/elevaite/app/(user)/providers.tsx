"use client";

import { ColorContext, AppDrawerTheme } from "@elevaite/ui";

export function Providers({ children }) {
  return <ColorContext.Provider value={AppDrawerTheme}>{children}</ColorContext.Provider>;
}
