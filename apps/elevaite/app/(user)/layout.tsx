import type { SidebarIconObject } from "@repo/ui/components";
import { ElevaiteIcons } from "@repo/ui/components";
import type { Metadata } from "next";
import AppLayout from "../ui/AppLayout";
import "./layout.css";
import { auth } from "../../auth";

export const metadata: Metadata = {
  title: "ElevAIte",
  description: "ElevAIte home",
};

const breadcrumbLabels: Record<string, { label: string; link: string }> = {
  // models: {
  //   label: "Models",
  //   link: "/models",
  // },
  // datasets: {
  //   label: "Datasets",
  //   link: "/datasets",
  // },
  access: {
    label: "Access Management",
    link: "/access",
  },
  workbench: {
    label: "Studio",
    link: "/workbench",
  },
  // cost: {
  //   label: "Billing and Costs",
  //   link: "/cost",
  // },
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
  // contracts: {
  //   label: "Contracts",
  //   link: "/contracts",
  // },
  // config: {
  //   label: "Config",
  //   link: "/config",
  // },
  // dashboard: {
  //   label: "Dashboard",
  //   link: "/dashboard",
  // },
};

const sidebarIcons: SidebarIconObject[] = [
  {
    icon: <ElevaiteIcons.SVGAccess />,
    link: "/access",
    description: "Access Management",
  },
  // {
  //   icon: <ElevaiteIcons.Datasets />,
  //   link: "/datasets",
  //   description: "Datasets",
  // },
  // { icon: <ElevaiteIcons.SVGModels />, link: "/models", description: "Models" },
  {
    icon: <ElevaiteIcons.Workbench />,
    link: "/workbench",
    description: "Workbench",
  },
  // {
  //   icon: <ElevaiteIcons.SVGCost />,
  //   link: "/cost",
  //   description: "Billing & Costs",
  // },
  {
    icon: <ElevaiteIcons.SVGApplications />,
    link: "/",
    description: "Applications",
  },
  // {
  //   icon: <ElevaiteIcons.SVGSettings />,
  //   link: "https://playground-dev.iopex.ai",
  //   description: "Config",
  // },
  // {
  //   icon: <ElevaiteIcons.SVGProjects className="rotate-180" />,
  //   link: "/dashboard",
  //   description: "Dashboard",
  // },
];

const alcatelSidebarIcons: SidebarIconObject[] = [
  {
    icon: <ElevaiteIcons.SVGApplications />,
    link: "/",
    description: "Applications",
  },
];

export default async function PageLayout({
  children,
}: {
  children: React.ReactNode;
}): Promise<JSX.Element> {
  // In development mode, use default sidebar icons
  if (process.env.NODE_ENV === "development") {
    return (
      <AppLayout
        breadcrumbLabels={breadcrumbLabels}
        layout="user"
        sidebarIcons={sidebarIcons}
      >
        {children}
      </AppLayout>
    );
  }

  // In production, use real auth
  const session = await auth();

  const isAlcatel = session?.user?.accountMemberships
    ? session.user.accountMemberships.filter(
        (membership) =>
          membership.account_id === "ab5eed01-46f1-423d-9da0-093814a898fc"
      ).length > 0
    : false;

  return (
    <AppLayout
      breadcrumbLabels={breadcrumbLabels}
      layout="user"
      sidebarIcons={isAlcatel ? alcatelSidebarIcons : sidebarIcons}
    >
      {children}
    </AppLayout>
  );
}
