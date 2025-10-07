"use client";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";
import { AppLayout } from "./AppLayout";

interface ConditionalLayoutProps {
  children: ReactNode;
}

export function ConditionalLayout({ children }: ConditionalLayoutProps): JSX.Element {
  const pathname = usePathname();

  // Pages that should NOT have the AppLayout (navbar, etc.)
  const authPages = ["/login", "/reset-password"];
  const dashboardPages = ["/", "/dashboard"]; // Add dashboard pages here

  const isAuthPage = authPages.includes(pathname);
  const isDashboardPage = dashboardPages.includes(pathname);

  // Don't apply AppLayout to auth pages or dashboard pages
  if (isAuthPage || isDashboardPage) {
    return <>{children}</>;
  }

  // For all other pages, use the AppLayout
  const breadcrumbs: Record<string, { label: string; link: string }> = {
    home: {
      label: "Analytics Dashboard",
      link: "/",
    },
  };

  return (
    <AppLayout breadcrumbs={breadcrumbs}>
      {children}
    </AppLayout>
  );
}