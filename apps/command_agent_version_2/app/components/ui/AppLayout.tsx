import { PortalRoot } from "@repo/ui";
import { type ReactNode, type JSX } from "react";
import "./AppLayout.scss";
import { CommandAgentHeader } from "./CommandAgentHeader";



interface AppLayoutProps {
    children: ReactNode,
}

export function AppLayout({children}: AppLayoutProps): JSX.Element {
    return (
        <>
            <PortalRoot />
            <div className="agent-version-2-app-layout-container">
                <CommandAgentHeader/>
                {children}
            </div>
        </>
    );
}