import { ElevaiteIcons, type SidebarIconObject } from "@repo/ui/components";
import { ColorContextProvider } from "@repo/ui/contexts";
import { RolesContextProvider } from "../lib/contexts/RolesContext";
import AppLayout from "../ui/AppLayout";
import { SessionProvider } from "next-auth/react";

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
    link: "/contracts",
  },
};

const sidebarIcons: SidebarIconObject[] = [
  {
    icon: <ElevaiteIcons.SVGAccess />,
    link: "/access",
    description: "Access Management",
  },
  {
    icon: <ElevaiteIcons.SVGApplications />,
    link: "/",
    description: "Applications",
  },
];

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}): JSX.Element {
  return (
    <SessionProvider>
      <RolesContextProvider>
        <ColorContextProvider>
          <AppLayout
            breadcrumbLabels={breadcrumbLabels}
            sidebarIcons={sidebarIcons}
          >
            {children}
          </AppLayout>
        </ColorContextProvider>
      </RolesContextProvider>
    </SessionProvider>
  );
}
