import type { SidebarIconObject } from "@repo/ui/components";
import { ElevaiteIcons } from "@repo/ui/components";
import { WorkbenchContextProvider } from "../lib/contexts/WorkbenchContext";
import AppLayout from "../ui/AppLayout";
import "./layout.css";



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
    // { icon: <ElevaiteIcons.WorkersQueues />, link: "/workers_queues" },
    { icon: <ElevaiteIcons.SVGAccess />, link: "/access", description: "Access Management" },
    { icon: <ElevaiteIcons.Datasets />, link: "/datasets", description: "Datasets" },
    { icon: <ElevaiteIcons.SVGModels />, link: "/models", description: "Models" },
    { icon: <ElevaiteIcons.Workbench />, link: "/workbench", description: "Workbench" },
    { icon: <ElevaiteIcons.SVGCost />, link: "/cost", description: "Billing & Costs" },
    { icon: <ElevaiteIcons.SVGApplications />, link: "/", description: "Applications" },
    { icon: <ElevaiteIcons.SVGSettings />, link: "https://playground-dev.iopex.ai", description: "Config"},
    { icon: <ElevaiteIcons.SVGProjects className="rotate-180"  />, link: "/dashboard", description: "Dashboard" },
];



export default function PageLayout({ children }: { children: React.ReactNode }): JSX.Element {
    return (
        <WorkbenchContextProvider>
            <AppLayout breadcrumbLabels={breadcrumbLabels} layout="engineer" sidebarIcons={sidebarIcons}>
                {children}
            </AppLayout>
        </WorkbenchContextProvider>
    );
}
