"use client";

import { ElevaiteIcons, type SidebarIconObject } from "@repo/ui/components";
import { ColorContextProvider, ThemeObject } from "@repo/ui/contexts";
import { useSession } from "next-auth/react";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
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
}

export function LayoutWrapper({ children, customThemes }: LayoutWrapperProps): JSX.Element {
  console.log("[LayoutWrapper] received themes:", customThemes);
  const { data: session } = useSession();
  const pathname = usePathname();
  const [isStylesLoaded, setIsStylesLoaded] = useState(false);

  // Ensure styles are loaded before rendering to prevent FOUC
  useEffect(() => {
    // Check if critical CSS variables are available
    const checkStyles = () => {
      const computedStyle = getComputedStyle(document.documentElement);
      const hasEvColors = computedStyle.getPropertyValue("--ev-colors-background");
      const hasNavbarHeight = computedStyle.getPropertyValue("--navbar-height");

      if (hasEvColors && hasNavbarHeight) {
        setIsStylesLoaded(true);
      } else {
        // Retry after a short delay
        setTimeout(checkStyles, 50);
      }
    };

    checkStyles();
  }, []);

  const isSuperAdmin = (session?.user as any)?.is_superuser === true;
  const isApplicationAdmin = (session?.user as any)?.application_admin === true;
  const isAnyAdmin = isSuperAdmin || isApplicationAdmin;

  const shouldShowSidebar = isSuperAdmin;

  // Check if we're on a page that should show admin layout
  const shouldShowAdminLayout =
    isAnyAdmin &&
    (pathname === "/" ||
      pathname.startsWith("/access") ||
      pathname.startsWith("/(admin)"));

  // Show loading state until styles are ready
  if (!isStylesLoaded) {
    return (
      <div
        style={{
          backgroundColor: "#161616",
          minHeight: "100vh",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          color: "#ffffff",
        }}
      >
        Loading...
      </div>
    );
  }

  return (
    <ColorContextProvider themes={customThemes}>
      {shouldShowAdminLayout ? (
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
    </ColorContextProvider>
  );
  
}
