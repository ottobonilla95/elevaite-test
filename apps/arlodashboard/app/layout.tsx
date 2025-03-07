import { ColorContextProvider } from "@repo/ui/contexts";
import type { Metadata } from "next";
import { SessionProvider } from "next-auth/react";
import { Inter } from "next/font/google";
import { auth } from "../auth";
import { AppLayout } from "./components/AppLayout";
import "./globals.css";
import { ChatContextProvider } from "./ui/contexts/ChatContext";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Arlo dashboard",
  description: "ElevAIte's Chatbot, ready to answer your questions!",
};

export default async function RootLayout({ children, }: Readonly<{ children: React.ReactNode; }>): Promise<JSX.Element> {
  const session = await auth();
  const breadcrumbs: Record<string, { label: string; link: string }> = {
    home: {
      label: "Arlo dashboard",
      link: "/",
    },
  };

  return (
    <html lang="en">
      <body className={inter.className}>

        <SessionProvider session={session}>
          <ColorContextProvider>
            <ChatContextProvider>

              <AppLayout breadcrumbs={breadcrumbs}>
                {children}
              </AppLayout>

            </ChatContextProvider>
          </ColorContextProvider>
        </SessionProvider>

      </body>
    </html>
  );
}
