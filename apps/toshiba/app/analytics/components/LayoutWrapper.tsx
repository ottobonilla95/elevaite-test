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
    label: "Analytics Dashboard",
    link: "/",
  },
};

const baseSidebarIcons: SidebarIconObject[] = [
  {
    icon: <ElevaiteIcons.SVGAccess />,
    link: "/access",
    description: "Access Management",
  },
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

  // Dashboard pages - navbar only, no sidebar
  const dashboardPages = ["/", "/dashboard", "/analytics"];
  const isDashboardPage = dashboardPages.includes(pathname);

  // Admin pages - full layout with sidebar
  const adminPages = ["/access", "/(admin)"];
  const isAdminPage = adminPages.some(page => pathname.startsWith(page));

  return (
    <ColorContextProvider themes={customThemes} hideDefaultThemes>
      {isAdminPage ? (
        // Full admin layout with sidebar
        <RolesContextProvider>
          <ClientAppLayout
            breadcrumbLabels={breadcrumbLabels}
            sidebarIcons={baseSidebarIcons}
          >
            {children}
          </ClientAppLayout>
        </RolesContextProvider>
      ) : isDashboardPage ? (
        // Dashboard with navbar but no sidebar
        <RolesContextProvider>
          <div className="elevaite-main-container" id="elevaite-main-container">
            <NavBar breadcrumbLabels={breadcrumbLabels} user={effectiveSession?.user} />
            <div className="children-container" style={{ gridColumn: "1 / -1" }}>
              {children}
            </div>
          </div>
        </RolesContextProvider>
      ) : (
        // No layout wrapper
        children
      )}
      <MfaGracePeriodToast />
    </ColorContextProvider>
  );
}




