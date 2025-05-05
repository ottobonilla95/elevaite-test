import type { SidebarIconObject } from "@repo/ui/components";
import { Sidebar } from "@repo/ui/components";
import { auth } from "../../auth";
import "./AppLayout.scss";
import { NavBar } from "./NavBar";


interface AppLayoutProps {
    sidebarIcons: SidebarIconObject[];
    Background?: React.ReactNode;
    children: React.ReactNode;
    breadcrumbLabels: Record<string, { label: string; link: string }>;
}

async function AppLayout({ sidebarIcons, children, breadcrumbLabels, ...props }: AppLayoutProps): Promise<JSX.Element> {
    const session = await auth();



    return (
        <div className="elevaite-main-container" id="elevaite-main-container">
            <NavBar
                breadcrumbLabels={breadcrumbLabels}
                user={session?.user}
            />
            <Sidebar sidebarIcons={sidebarIcons} />
            <div className="children-container">
                {children}
            </div>
        </div>
    );
}

export default AppLayout;
