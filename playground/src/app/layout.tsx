import "./globals.css";
import type { Metadata } from "next";
import { Inter } from "next/font/google";
import PageHeader from "../components/pageheader/pageheader";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Playground",
  description: "Experiment with different llms and vector databases",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <PageHeader />
        {children}
      </body>
    </html>
  );
}
