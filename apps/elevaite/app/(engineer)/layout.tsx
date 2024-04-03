import type { SidebarIconObject } from "@repo/ui/components";
import { ElevaiteIcons } from "@repo/ui/components";
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
    // { icon: <ElevaiteIcons.Datasets />, link: "/datasets" },
    // { icon: <ElevaiteIcons.WorkersQueues />, link: "/workers_queues" },
    { icon: <ElevaiteIcons.SVGModels />, link: "/models", description: "Models" },
    { icon: <ElevaiteIcons.Workbench />, link: "/workbench", description: "Workbench" },
    { icon: <ElevaiteIcons.SVGApplications />, link: "/", description: "Applications" },
];



export default function PageLayout({ children }: { children: React.ReactNode }): JSX.Element {
    return (
        <AppLayout breadcrumbLabels={breadcrumbLabels} layout="engineer" sidebarIcons={sidebarIcons}>
            {children}
        </AppLayout>
    );
}
