import { ColorContextProvider } from "@repo/ui/contexts";
import type { Metadata } from "next";
import { SessionProvider } from "next-auth/react";
import { Inter } from "next/font/google";
import { auth } from "../auth";
import { AppLayout } from "./components/AppLayout";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "ElevAIte Pipeline",
  description: "ElevAIte's Pipeline Visualization and Management",
};

export default async function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>): Promise<JSX.Element> {
  const session = await auth();
  const breadcrumbs: Record<string, { label: string; link: string }> = {
    home: {
      label: "Pipeline",
      link: "/",
    },
  };

  return (
    <html lang="en" style={{ backgroundColor: "#000" }}>
      <body
        className={inter.className}
        style={{ backgroundColor: "#000", background: "#000" }}
      >
        <SessionProvider session={session}>
          <ColorContextProvider>
            <AppLayout breadcrumbs={breadcrumbs}>{children}</AppLayout>
          </ColorContextProvider>
        </SessionProvider>
      </body>
    </html>
  );
}
