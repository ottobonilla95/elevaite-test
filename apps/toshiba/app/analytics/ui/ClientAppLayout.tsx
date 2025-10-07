"use client";

import type { SidebarIconObject } from "@repo/ui/components";
import { Sidebar } from "@repo/ui/components";
import "./AppLayout.scss";
import { NavBar } from "./NavBar";
import { useSession } from "next-auth/react";

interface ClientAppLayoutProps {
  sidebarIcons: SidebarIconObject[];
  Background?: React.ReactNode;
  children: React.ReactNode;
  breadcrumbLabels: Record<string, { label: string; link: string }>;
}

export function ClientAppLayout({
  sidebarIcons,
  children,
  breadcrumbLabels,
  ...props
}: ClientAppLayoutProps): JSX.Element {
  const { data: session } = useSession();

  return (
    <div className="elevaite-main-container" id="elevaite-main-container">
      <NavBar breadcrumbLabels={breadcrumbLabels} user={session?.user} />
      <Sidebar sidebarIcons={sidebarIcons} />
      <div className="children-container">{children}</div>
    </div>
  );
}
