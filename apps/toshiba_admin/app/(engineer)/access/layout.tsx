import type { Metadata } from "next";
import { RolesContextProvider } from "../../lib/contexts/RolesContext";

export const metadata: Metadata = {
  title: "Toshiba Admin Access Management",
  description: "View, add, and modify user roles and related access.",
};

export default function PageLayout({
  children,
}: {
  children: React.ReactNode;
}): JSX.Element {
  return <RolesContextProvider>{children}</RolesContextProvider>;
}
