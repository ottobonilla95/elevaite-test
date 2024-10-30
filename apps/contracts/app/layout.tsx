import { Inter } from "next/font/google";
import "./layout.scss";
import "./layout.css"
import Providers from "./ui/Providers";
import { Metadata } from "next";
import AppLayout from "./ui/AppLayout";
import { ElevaiteIcons, SidebarIconObject } from "@repo/ui/components";


const font = Inter({ subsets: ["latin"] });


interface RootLayoutProps {
    children: React.ReactNode
}

const breadcrumbLabels: Record<string, { label: string; link: string }> = {
  models: {
    label: "Models",
    link: "/models",
  },
  datasets: {
    label: "Datasets",
    link: "/datasets",
  },
  access: {
    label: "Access Management",
    link: "/access",
  },
  workbench: {
    label: "Workbench",
    link: "/workbench",
  },
  cost: {
      label: "Billing and Costs",
      link: "/cost",
  },
  application: {
    label: "Application",
    link: "/application",
  },
  home: {
    label: "Applications",
    link: "/",
  },
  homepage: {
    label: "Applications",
    link: "/",
  },
  contracts: {
    label: "Contracts",
    link: "/contracts"
  }
};

const sidebarIcons: SidebarIconObject[] = [
  { icon: <ElevaiteIcons.SVGAccess />, link: "/access", description: "Access Management" },
  { icon: <ElevaiteIcons.Datasets />, link: "/datasets", description: "Datasets" },
  { icon: <ElevaiteIcons.SVGModels />, link: "/models", description: "Models" },
  { icon: <ElevaiteIcons.Workbench />, link: "/workbench", description: "Workbench" },
  { icon: <ElevaiteIcons.SVGCost />, link: "/cost", description: "Billing & Costs" },
  { icon: <ElevaiteIcons.SVGApplications />, link: "/", description: "Applications" },
];



export const metadata: Metadata = {
    title: "Contract Co-Pilot",
    description: "Quickly discover and evaluate important data in your contracts and invoices.",
};

export default function RootLayout({children}: RootLayoutProps): JSX.Element {

    return (
        <html lang="en">
            <body className={font.className}>
                <Providers>
                    <AppLayout breadcrumbLabels={breadcrumbLabels} layout="user" sidebarIcons={sidebarIcons}>
                    {children}
                    </AppLayout>
                </Providers>
            </body>
        </html>
    );
}