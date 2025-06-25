"use client";
import { useState } from "react";
import { useRoles } from "../lib/contexts/RolesContext";
// Define the enum locally to avoid import issues
enum ACCESS_MANAGEMENT_TABS {
  ACCOUNTS = "Accounts",
  PROJECTS = "Projects",
  USERS = "Users",
  ROLES = "Roles",
}
import { AccessHeader } from "./components/AccessHeader";
import { AccessTabs } from "./components/AccessTabs";
import "./page.scss";

export default function Page(): JSX.Element {
  const rolesContext = useRoles();
  const [selectedTab, setSelectedTab] = useState<ACCESS_MANAGEMENT_TABS>(
    ACCESS_MANAGEMENT_TABS.ACCOUNTS
  );

  function handleRefresh() {
    rolesContext.refresh(selectedTab);
  }

  return (
    <div className="access-main-container">
      <AccessHeader onRefresh={handleRefresh} selectedTab={selectedTab} />
      <AccessTabs selectedTab={selectedTab} setSelectedTab={setSelectedTab} />
    </div>
  );
}
