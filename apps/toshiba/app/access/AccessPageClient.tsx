"use client";
import { useState } from "react";
import { useSession } from "next-auth/react";
import { useRoles } from "../lib/contexts/RolesContext";

enum ACCESS_MANAGEMENT_TABS {
  ACCOUNTS = "Accounts",
  PROJECTS = "Projects",
  USERS = "Users",
  ROLES = "Roles",
}
import { AccessHeader } from "./components/AccessHeader";
import { AccessTabs } from "./components/AccessTabs";
import "./page.scss";

export default function AccessPageClient({
  isSuperAdmin,
}: {
  isSuperAdmin: boolean;
}): JSX.Element {
  const { data: session } = useSession();
  const rolesContext = useRoles();

  const isApplicationAdmin = (session?.user as any)?.application_admin === true;

  // Default to Users tab for application admins, Accounts tab for superusers
  const defaultTab =
    isApplicationAdmin && !isSuperAdmin
      ? ACCESS_MANAGEMENT_TABS.USERS
      : ACCESS_MANAGEMENT_TABS.ACCOUNTS;

  const [selectedTab, setSelectedTab] =
    useState<ACCESS_MANAGEMENT_TABS>(defaultTab);

  function handleRefresh() {
    rolesContext.refresh(selectedTab);
  }

  return (
    <div className="access-main-container">
      <AccessHeader onRefresh={handleRefresh} selectedTab={selectedTab} />
      <AccessTabs
        selectedTab={selectedTab}
        setSelectedTab={setSelectedTab}
        isSuperAdmin={isSuperAdmin}
      />
    </div>
  );
}
