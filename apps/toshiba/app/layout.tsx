import { ThemeObject, ThemeType, ToshibaDark, ToshibaLight } from "@repo/ui/contexts";
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
  { id: "toshibaDarkTheme01", label: "Toshiba Dark Theme", type: ThemeType.DARK, colors: ToshibaDark },
  { id: "toshibaLightTheme01", label: "Toshiba Light Theme", type: ThemeType.LIGHT, colors: ToshibaLight },
]

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
      <head>
        <style
          dangerouslySetInnerHTML={{
            __html: `
              /* Critical CSS to prevent FOUC */
              :root {
                --sidebar-width: 48px;
                --navbar-height: 52px;
                --ev-colors-primary: #282828;
                --ev-colors-secondary: #424242;
                --ev-colors-tertiary: #4e332a;
                --ev-colors-highlight: #e75f33;
                --ev-colors-text: #ffffff;
                --ev-colors-secondaryText: #808080;
                --ev-colors-tertiaryText: #a3a3a3;
                --ev-colors-borderColor: #ffffff1f;
                --ev-colors-background: #161616;
                --ev-colors-success: #d8fc77;
                --ev-colors-danger: #dc143c;
                font-family: Inter;
              }
              body {
                background-color: var(--ev-colors-background);
                color: var(--ev-colors-text);
                margin: 0;
                padding: 0;
              }
            `,
          }}
        />
      </head>
      <body className={inter.className}>
        <SessionProvider session={session}>
          <SessionValidator>
            <LayoutWrapper customThemes={toshibaThemes}>
              {children}
            </LayoutWrapper>
          </SessionValidator>
        </SessionProvider>
      </body>
    </html>
  );
}
