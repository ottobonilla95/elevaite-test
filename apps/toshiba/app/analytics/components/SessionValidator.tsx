"use client";

import { useSessionValidation } from "../hooks/useSessionValidation";

export function SessionValidator({
  children,
}: {
  children: React.ReactNode;
}): JSX.Element {
  useSessionValidation();

  return <>{children}</>;
}
