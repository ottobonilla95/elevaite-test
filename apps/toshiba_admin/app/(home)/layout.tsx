import type { Metadata } from "next";
import { ElevaiteIcons, type SidebarIconObject } from "@repo/ui/components";
import { RolesContextProvider } from "../lib/contexts/RolesContext";
import AppLayout from "../ui/AppLayout";
import { ColorContextProvider } from "@repo/ui/contexts";

export const metadata: Metadata = {
  title: "Toshiba Admin Access Management",
  description: "View, add, and modify user roles and related access.",
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
  access: {
    label: "Access Management",
    link: "/access",
  },
  datasets: {
    label: "Datasets",
    link: "/datasets",
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
  { icon: <ElevaiteIcons.SVGApplications />, link: "/", description: "Applications" },
  { icon: <ElevaiteIcons.SVGSettings />, link: "https://playground-dev.iopex.ai", description: "Config" },
];

export default function PageLayout({
  children,
}: {
  children: React.ReactNode;
}): JSX.Element {
  return <RolesContextProvider>
    <ColorContextProvider>
      <AppLayout breadcrumbLabels={breadcrumbLabels} sidebarIcons={sidebarIcons}>
        {children}
      </AppLayout>
    </ColorContextProvider>
  </RolesContextProvider>;
}
