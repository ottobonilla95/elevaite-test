"use client";

import { useSession } from "next-auth/react";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
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
  const [isStylesLoaded, setIsStylesLoaded] = useState(false);

  // Ensure styles are loaded before rendering to prevent FOUC
  useEffect(() => {
    // Check if critical CSS variables are available
    const checkStyles = () => {
      const computedStyle = getComputedStyle(document.documentElement);
      const hasEvColors = computedStyle.getPropertyValue(
        "--ev-colors-background"
      );
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

  // Check if user is admin
  const isAdmin = (session?.user as any)?.is_superuser === true;

  // Check if we're on a page that should show admin layout
  const shouldShowAdminLayout =
    isAdmin &&
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
