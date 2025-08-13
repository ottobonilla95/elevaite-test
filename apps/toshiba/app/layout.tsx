import {
  ThemeObject,
  ThemeType,
  ToshibaDark,
  ToshibaLight,
} from "@repo/ui/contexts";
import "@repo/ui/styles.css";
import type { Metadata } from "next";
import { SessionProvider } from "next-auth/react";
import { Inter } from "next/font/google";
import { auth } from "../auth";
import { LayoutWrapper } from "./components/LayoutWrapper";
import { SessionValidator } from "./components/SessionValidator";
import "./ui/globals.css";

// Force dynamic rendering for all pages
export const dynamic = "force-dynamic";

const inter = Inter({ subsets: ["latin"] });

const toshibaThemes: ThemeObject[] = [
  {
    id: "toshibaDarkTheme01",
    label: "Toshiba Dark Theme",
    type: ThemeType.DARK,
    colors: ToshibaDark,
  },
  {
    id: "toshibaLightTheme01",
    label: "Toshiba Light Theme",
    type: ThemeType.LIGHT,
    colors: ToshibaLight,
  },
];

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
      <head></head>
      <body className={inter.className}>
        <SessionProvider session={session}>
          <SessionValidator>
            <LayoutWrapper
              customThemes={toshibaThemes}
              initialSession={session}
            >
              {children}
            </LayoutWrapper>
          </SessionValidator>
        </SessionProvider>
      </body>
    </html>
  );
}
