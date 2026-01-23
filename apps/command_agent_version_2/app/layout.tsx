import { ColorContextProvider } from "@repo/ui/contexts";
import { ReactFlowProvider } from "@xyflow/react";
import type { Metadata } from "next";
import { SessionProvider } from "next-auth/react";
import { DM_Sans as FontDMSans } from "next/font/google";
import { auth } from "../auth";
import { AppLayout } from "./components/ui/AppLayout";
import "./globals.css";
import { CanvasContextProvider } from "./lib/contexts/CanvasContext";
import { ConfigPanelContextProvider } from "./lib/contexts/ConfigPanelContext";


import type { JSX } from "react";


const currentFont = FontDMSans({ subsets: ["latin"], display: "swap" });

export const metadata: Metadata = {
	title: "ElevAIte's Command Agent",
	description: "ElevAIte's canvas, ready to tailor agents and tools to your needs!",
};

export default async function RootLayout({ children, }: Readonly<{ children: React.ReactNode; }>): Promise<JSX.Element> {
	const session = await auth();

	return (
		<html lang="en" className={currentFont.className} suppressHydrationWarning>
		<body>
			<SessionProvider session={session}>
				<ColorContextProvider>
					<CanvasContextProvider>
						<ConfigPanelContextProvider>
							<ReactFlowProvider>
								<AppLayout>
									{children}
								</AppLayout>
							</ReactFlowProvider>
						</ConfigPanelContextProvider>
					</CanvasContextProvider>
				</ColorContextProvider>
			</SessionProvider>
		</body>
		</html>
	);
}
