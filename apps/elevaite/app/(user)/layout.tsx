import type { SidebarIconObject } from "@repo/ui/components";
import { ElevaiteIcons } from "@repo/ui/components";
import type { Metadata } from "next";
import AppLayout from "../ui/AppLayout";
import "./layout.css";



export const metadata: Metadata = {
  title: "ElevAIte",
  description: "ElevAIte home",
};

const breadcrumbLabels: Record<string, { label: string; link: string }> = {
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
  homepage: {
    label: "Applications",
    link: "/",
  },
};

const sidebarIcons: SidebarIconObject[] = [
  { icon: <ElevaiteIcons.Datasets />, link: "/datasets", description: "Datasets" },
  { icon: <ElevaiteIcons.SVGModels />, link: "/models", description: "Models" },
  { icon: <ElevaiteIcons.Workbench />, link: "/workbench", description: "Workbench" },
  { icon: <ElevaiteIcons.SVGApplications />, link: "/", description: "Applications" },
];



export default function PageLayout({ children }: { children: React.ReactNode }): JSX.Element {
  return (
    <AppLayout breadcrumbLabels={breadcrumbLabels} layout="user" sidebarIcons={sidebarIcons}>
      {children}
    </AppLayout>
  );
}
