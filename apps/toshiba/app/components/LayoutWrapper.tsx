"use client";

import { useSession } from "next-auth/react";
import { usePathname } from "next/navigation";
import { ElevaiteIcons, type SidebarIconObject } from "@repo/ui/components";
import { ColorContextProvider } from "@repo/ui/contexts";
import { RolesContextProvider } from "../lib/contexts/RolesContext";
import { ClientAppLayout } from "../ui/ClientAppLayout";

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

const sidebarIcons: SidebarIconObject[] = [
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
];

interface LayoutWrapperProps {
  children: React.ReactNode;
}

export function LayoutWrapper({ children }: LayoutWrapperProps): JSX.Element {
  const { data: session } = useSession();
  const pathname = usePathname();

  // Check if user is admin
  const isAdmin = (session?.user as any)?.is_superuser === true;

  // Check if we're on a page that should show admin layout
  const shouldShowAdminLayout =
    isAdmin &&
    (pathname === "/" ||
      pathname.startsWith("/access") ||
      pathname.startsWith("/(admin)"));

  if (shouldShowAdminLayout) {
    return (
      <RolesContextProvider>
        <ColorContextProvider>
          <ClientAppLayout
            breadcrumbLabels={breadcrumbLabels}
            sidebarIcons={sidebarIcons}
          >
            {children}
          </ClientAppLayout>
        </ColorContextProvider>
      </RolesContextProvider>
    );
  }

  // For non-admin users or non-admin pages, return children directly
  return <>{children}</>;
}
