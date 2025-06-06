import { ColorContextProvider } from "@repo/ui/contexts";
import type { Metadata } from "next";
import { SessionProvider } from "next-auth/react";
import { Inter } from "next/font/google";
import { auth } from "../auth";
import { AppLayout } from "./components/AppLayout";
import "./globals.css";
import { ChatContextProvider } from "./ui/contexts/ChatContext";
import { ToolsProvider } from "./ui/contexts/ToolsContext";

const inter = Inter({ subsets: ["latin"], display: "swap" });

export const metadata: Metadata = {
  title: "Agentic AI",
  description: "ElevAIte's Chatbot, ready to answer your questions!",
};

export default async function RootLayout({ children, }: Readonly<{ children: React.ReactNode; }>): Promise<JSX.Element> {
  const session = await auth();
  const breadcrumbs: Record<string, { label: string; link: string }> = {
    home: {
      label: "Command Agent",
      link: "/",
    },
  };

  return (
    <html lang="en" className={inter.className}>
      <body>

        <SessionProvider session={session}>
          <ColorContextProvider>
            <ChatContextProvider>
              <ToolsProvider>

                <AppLayout breadcrumbs={breadcrumbs}>
                  {children}
                </AppLayout>

              </ToolsProvider>
            </ChatContextProvider>
          </ColorContextProvider>
        </SessionProvider>

      </body>
    </html>
  );
}
