"use client";

import { ElevaiteIcons, type SidebarIconObject } from "@repo/ui/components";
import { ColorContextProvider, ThemeObject } from "@repo/ui/contexts";
import { useSession } from "next-auth/react";
import type { Session } from "next-auth";
import { usePathname } from "next/navigation";
import { RolesContextProvider } from "../lib/contexts/RolesContext";
import { ClientAppLayout } from "../ui/ClientAppLayout";
import { MfaGracePeriodToast } from "./MfaGracePeriodToast";
import { NavBar } from "../ui/NavBar";

const breadcrumbLabels: Record<string, { label: string; link: string }> = {
  access: {
    label: "Access Management",
    link: "/access",
  },
  home: {
    label: "Applications",
    link: "/",
  },
};

interface LayoutWrapperProps {
  customThemes?: ThemeObject[];
  children: React.ReactNode;
  initialSession?: Session | null;
}

export function LayoutWrapper({
  children,
  customThemes,
  initialSession,
}: LayoutWrapperProps): JSX.Element {
  const { data: session } = useSession();
  const pathname = usePathname();

  const effectiveSession = initialSession || session;

  const isSuperAdmin = (effectiveSession?.user as any)?.is_superuser === true;
  const isApplicationAdmin =
    (effectiveSession?.user as any)?.application_admin === true;
  const isAnyAdmin = isSuperAdmin || isApplicationAdmin;
  const isManager = (effectiveSession?.user as any)?.is_manager === true;

  const shouldShowSidebar = isAnyAdmin || isManager;

  // Build sidebar icons with conditional disabled state
  const baseSidebarIcons: SidebarIconObject[] = [
    ...(isAnyAdmin ? [{
      icon: <ElevaiteIcons.SVGAccess />,
      link: "/access",
      description: "Access Management",
    }] : []),
    {
      icon: <ElevaiteIcons.SVGApplications />,
      link: "/",
      description: "Applications",
    },
    {
      icon: <ElevaiteIcons.SVGSettings />,
      link: "/settings",
      description: "Settings",
    },
  ];

  // Check if we're on a page that should show admin layout
  const shouldShowAdminLayout =
    (isAnyAdmin || isManager) &&
    (pathname === "/" ||
      pathname.startsWith("/access") ||
      pathname.startsWith("/(admin)"));

  const shouldRenderAdminLayout = shouldShowAdminLayout;

  return (
    <ColorContextProvider themes={customThemes} hideDefaultThemes>
      {shouldRenderAdminLayout ? (
        <RolesContextProvider>
          <ClientAppLayout
            breadcrumbLabels={breadcrumbLabels}
            sidebarIcons={shouldShowSidebar ? baseSidebarIcons : []}
          >
            {children}
          </ClientAppLayout>
        </RolesContextProvider>
      ) : pathname === "/analytics" ? (
        // Analytics page with navbar but no sidebar
        <RolesContextProvider>
          <div className="elevaite-main-container" id="elevaite-main-container">
            <NavBar breadcrumbLabels={breadcrumbLabels} user={effectiveSession?.user} />
            <div className="children-container" style={{ gridColumn: "1 / -1" }}>
              {children}
            </div>
          </div>
        </RolesContextProvider>
      ) : (
        children
      )}
      <MfaGracePeriodToast />
    </ColorContextProvider>
  );
}