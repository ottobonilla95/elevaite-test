import type { Metadata } from "next";
import { SessionProvider } from "next-auth/react";
import { Inter } from "next/font/google";
import "./ui/globals.css";
import "@repo/ui/styles.css";
import { auth } from "../auth";
import { SessionValidator } from "./components/SessionValidator";
import { LayoutWrapper } from "./components/LayoutWrapper";

// Force dynamic rendering for all pages
export const dynamic = "force-dynamic";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "ElevAIte Chat",
  description: "ElevAIte's Chatbot, ready to answer your questions!",
};

export default async function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>): Promise<JSX.Element> {
  const session = await auth();
  return (
    <html lang="en">
      <body className={inter.className}>
        <SessionProvider session={session}>
          <SessionValidator>
            <LayoutWrapper>{children}</LayoutWrapper>
          </SessionValidator>
        </SessionProvider>
      </body>
    </html>
  );
}
