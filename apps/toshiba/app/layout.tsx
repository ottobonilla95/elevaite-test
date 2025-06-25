import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./ui/globals.css";
import "@repo/ui/styles.css";
import { ElevaiteIcons, type SidebarIconObject } from "@repo/ui/components";
import { ColorContextProvider } from "@repo/ui/contexts";
import { RolesContextProvider } from "./lib/contexts/RolesContext";
import AppLayout from "./ui/AppLayout";
import { SessionProvider } from "next-auth/react";
import { auth } from "../auth";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Toshiba",
  description: "Toshiba Application",
};

const breadcrumbLabels: Record<string, { label: string; link: string }> = {
  access: {
    label: "Access Management",
    link: "/access",
  },
  home: {
    label: "Applications",
    link: "/",
  },
};

const sidebarIcons: SidebarIconObject[] = [
  {
    icon: <ElevaiteIcons.SVGAccess />,
    link: "/access",
    description: "Access Management",
  },
  {
    icon: <ElevaiteIcons.SVGApplications />,
    link: "/",
    description: "Applications",
  },
];

export default async function RootLayout({
  children,
}: {
  children: React.ReactNode;
}): Promise<JSX.Element> {
  const session = await auth();

  // Check if user is admin
  const isAdmin =
    session?.user?.email?.includes("admin") ||
    (session?.user as any)?.role === "admin" ||
    (session?.user as any)?.is_superuser === true;

  return (
    <html lang="en">
      <body className={inter.className}>
        <SessionProvider>
          {isAdmin ? (
            <RolesContextProvider>
              <ColorContextProvider>
                <AppLayout
                  breadcrumbLabels={breadcrumbLabels}
                  sidebarIcons={sidebarIcons}
                >
                  {children}
                </AppLayout>
              </ColorContextProvider>
            </RolesContextProvider>
          ) : (
            children
          )}
        </SessionProvider>
      </body>
    </html>
  );
}
