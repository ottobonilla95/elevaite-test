"use client";

import { ElevaiteIcons, type SidebarIconObject } from "@repo/ui/components";
import { ColorContextProvider, ThemeObject } from "@repo/ui/contexts";
import { useSession } from "next-auth/react";
import type { Session } from "next-auth";
import { usePathname } from "next/navigation";
import { RolesContextProvider } from "../lib/contexts/RolesContext";
import { ClientAppLayout } from "../ui/ClientAppLayout";
import { MfaGracePeriodToast } from "./MfaGracePeriodToast";

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

  const shouldShowSidebar = isSuperAdmin;

  // Check if we're on a page that should show admin layout
  const shouldShowAdminLayout =
    isAnyAdmin &&
    (pathname === "/" ||
      pathname.startsWith("/access") ||
      pathname.startsWith("/(admin)"));

  const shouldRenderAdminLayout = shouldShowAdminLayout;

  return (
    <ColorContextProvider themes={customThemes}>
      {shouldRenderAdminLayout ? (
        <RolesContextProvider>
          <ClientAppLayout
            breadcrumbLabels={breadcrumbLabels}
            sidebarIcons={shouldShowSidebar ? baseSidebarIcons : []}
          >
            {children}
          </ClientAppLayout>
        </RolesContextProvider>
      ) : (
        children
      )}
      <MfaGracePeriodToast />
    </ColorContextProvider>
  );
}
