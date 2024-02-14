import { ElevaiteIcons, SidebarIconObject } from "@repo/ui/components";
import { ColorContextProvider } from "@repo/ui/contexts";
import type { Metadata } from "next";
import { SessionProvider } from "next-auth/react";
import { Inter } from "next/font/google";
import { auth } from "../../auth";
import AppLayout from "../ui/AppLayout";
import { AppDrawerTheme } from "../ui/themes";
import "./layout.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "ElevAIte",
  description: "ElevAIte home",
};

export default async function RootLayout({ children }: { children: React.ReactNode }): Promise<JSX.Element> {
  const breadcrumbLabels: Record<string, { label: string; link: string }> = {
    appDrawer: {
      label: "Applications",
      link: "/appDrawer",
    },
    home: {
      label: "Applications",
      link: "/",
    },
    homepage: {
      label: "Applications",
      link: "/",
    },
  };

  const sidebarIcons: SidebarIconObject[] = [
    { icon: <ElevaiteIcons.SVGApplications />, link: "/", description: "Applications" },
    // { icon: <ElevaiteIcons.Datasets />, link: "/datasets" },
    // { icon: <ElevaiteIcons.WorkersQueues />, link: "/workers_queues" },
    // { icon: <ElevaiteIcons.Models />, link: "/models" },
    { icon: <ElevaiteIcons.Workbench />, link: "/workbench", description: "Workbench" },
  ];

  const session = await auth();
  if (session?.user) {
    // @ts-expect-error TODO: Look into https://react.dev/reference/react/experimental_taintObjectReference
    // filter out sensitive data before passing to client.
    session.user = {
      name: session.user.name,
      email: session.user.email,
      image: session.user.image,
    };
  }

  return (
    <html lang="en">
      <body className={`${inter.className} bg-[${AppDrawerTheme.secondary}] -z-50`}>
        <SessionProvider session={session}>
          <ColorContextProvider theme={AppDrawerTheme}>
            <AppLayout
              breadcrumbLabels={breadcrumbLabels}
              layout="user"
              sidebarIcons={sidebarIcons}
            >
              {children}
            </AppLayout>
          </ColorContextProvider>
        </SessionProvider>
      </body>
    </html>
  );
}
