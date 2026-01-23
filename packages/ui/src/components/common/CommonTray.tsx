import type { JSX } from "react";
import "./CommonTray.scss";



interface CommonTrayProps {
    isOpen: boolean;
    children: React.ReactNode;
}

export function CommonTray({ isOpen, children }: CommonTrayProps): JSX.Element {
    return (
        <div className={["common-tray-container", isOpen ? "open" : undefined].filter(Boolean).join(" ")}>
            <div className="common-tray-content">
                {children}
            </div>
        </div>
    );
}