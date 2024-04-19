"use client";
import type { SidebarIconObject } from "@repo/ui/components";
import { NavBar, Sidebar } from "@repo/ui/components";
import { useSession } from "next-auth/react";
import { useState } from "react";
import { logOut } from "../lib/actions/generalActions";
import { engineerSearchHelper, userSearchHelper } from "../lib/searchHelpers";
import "./AppLayout.scss";


interface AppLayoutProps {
  sidebarIcons: SidebarIconObject[];
  layout: "user" | "engineer";
  Background?: React.ReactNode;
  children: React.ReactNode;
  breadcrumbLabels: Record<string, { label: string; link: string }>;
}

function AppLayout({
  sidebarIcons,
  children,
  breadcrumbLabels,
  ...props
}: AppLayoutProps): JSX.Element {
  const [results, setResults] = useState<{ key: string; link: string; label: string }[]>(getResults(""));
  const { data: session } = useSession();


  function getResults(term: string): { key: string; link: string; label: string }[] {
    switch (props.layout) {
      case "user": {
        return userSearchHelper(term);
      }
      case "engineer": {
        return engineerSearchHelper(term);
      }
      default: {
        // eslint-disable-next-line no-console -- TODO: Create custom logger
        console.log("Missing layout parameter");
        return [];
      }
    }
  }

  function handleSearchInput(term: string): void {
    setResults(getResults(term));
  }
  

  return (
    <div className="elevaite-main-container" id="elevaite-main-container">
      <NavBar
        breadcrumbLabels={breadcrumbLabels}
        handleSearchInput={handleSearchInput}
        logOut={logOut}
        searchResults={results}
        user={{ icon: session?.user?.image ?? "" }}
      />
      <Sidebar sidebarIcons={sidebarIcons} />
      <div className="children-container">
        {children}
      </div>
    </div>
  );
}

export default AppLayout;
