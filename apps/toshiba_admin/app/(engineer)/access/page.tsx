"use client";
import { useState } from "react";
import { useRoles } from "../../lib/contexts/RolesContext";
import { ACCESS_MANAGEMENT_TABS } from "../../lib/interfaces";
import { AccessHeader } from "./components/AccessHeader";
import { AccessTabs } from "./components/AccessTabs";
import "./page.scss";

export default function Page(): JSX.Element {
  const rolesContext = useRoles();
  const [selectedTab, setSelectedTab] = useState<ACCESS_MANAGEMENT_TABS>(ACCESS_MANAGEMENT_TABS.ACCOUNTS);
  
  function handleRefresh() {
    rolesContext.refresh(selectedTab);
  }

  return (
    <div className="access-main-container">
      <AccessHeader
        onRefresh={handleRefresh}
        selectedTab={selectedTab}
      />
      <AccessTabs 
        selectedTab={selectedTab}
        setSelectedTab={setSelectedTab}
      />
    </div>
  );
}
