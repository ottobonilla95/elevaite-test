"use client";
import { Logos, NavBar } from "@repo/ui/components";
import { useSession } from "next-auth/react";
import type { ReactNode } from "react";
import { clientLogout } from "../lib/clientLogout";
import "./AppLayout.scss";

interface AppLayoutProps {
  children: ReactNode;
  breadcrumbs: Record<string, { label: string; link: string }>;
}

export function AppLayout({
  children,
  breadcrumbs,
}: AppLayoutProps): JSX.Element {
  const { data: session } = useSession();

  const additionalMenuItems: never[] = [];

  return (
    <div className="chatbot-layout-container">
      <NavBar
        customLogo={<Logos.Toshiba />}
        customRightSide={
          <div className="right-side-logo">
            <img
              src="/icons/Maintenance_Services.png"
              alt="Maintenance Services"
            />
          </div>
        }
        breadcrumbLabels={breadcrumbs}
        logOut={clientLogout}
        user={{ image: session?.user?.image ?? "" }}
        additionalMenuItems={additionalMenuItems}
        hideHelp
      />
      {children}
    </div>
  );
}
