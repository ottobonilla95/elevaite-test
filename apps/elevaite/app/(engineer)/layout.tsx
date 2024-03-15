import type { SidebarIconObject } from "@repo/ui/components";
import { ElevaiteIcons } from "@repo/ui/components";
import { ColorContextProvider } from "@repo/ui/contexts";
import type { Metadata } from "next";
import { SessionProvider } from "next-auth/react";
import { Inter } from "next/font/google";
import { auth } from "../../auth";
import AppLayout from "../ui/AppLayout";
import { EngineerTheme } from "../ui/themes";
import "./layout.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
    title: "ElevAIte Workbench",
    description: "Ingest and Preprocess data at your convenience.",
};

const breadcrumbLabels: Record<string, { label: string; link: string }> = {
    workers_queues: {
        label: "Workers & Queues",
        link: "/workers_queues",
    },
    models: {
        label: "Models",
        link: "/models",
    },
    datasets: {
        label: "Datasets",
        link: "/datasets",
    },
    workbench: {
        label: "Workbench",
        link: "/workbench",
    },
    application: {
        label: "Application",
        link: "/application",
    },
    home: {
        label: "Applications",
        link: "/",
    },
};

const sidebarIcons: SidebarIconObject[] = [
    { icon: <ElevaiteIcons.SVGApplications />, link: "/", description: "Applications" },
    // { icon: <ElevaiteIcons.Datasets />, link: "/datasets" },
    // { icon: <ElevaiteIcons.WorkersQueues />, link: "/workers_queues" },
    { icon: <ElevaiteIcons.SVGModels />, link: "/models" },
    { icon: <ElevaiteIcons.Workbench />, link: "/workbench", description: "Workbench" },
];

export default async function RootLayout({ children }: { children: React.ReactNode }): Promise<JSX.Element> {
    const session = await auth();
    if (session?.user) {
        // filter out sensitive data before passing to client.
        session.user = {
            id: session.user.id,
            name: session.user.name,
            email: session.user.email,
            image: session.user.image,
        };
    }
    return (
        <html lang="en">
            <body className={inter.className}>
                <SessionProvider session={session}>
                    <ColorContextProvider theme={EngineerTheme}>
                        <AppLayout breadcrumbLabels={breadcrumbLabels} layout="engineer" sidebarIcons={sidebarIcons}>
                            {children}
                        </AppLayout>
                    </ColorContextProvider>
                </SessionProvider>
            </body>
        </html>
    );
}
