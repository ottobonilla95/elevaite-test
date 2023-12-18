"use client";
import { ColorContext, type ColorScheme } from "@repo/ui/contexts";
import { NavBar, Sidebar } from "@repo/ui/components";
import { useState } from "react";
import { engineerSearchHelper, userSearchHelper } from "../lib/searchHelpers";

interface AppLayoutProps {
  sidebarIcons: {
    linkLocation: string;
    Icon: React.ReactNode;
  }[];
  theme: ColorScheme;
  layout: "user" | "engineer";
  Background?: React.ReactNode;
  children: React.ReactNode;
  breadcrumbLabels: Record<string, { label: string; link: string }>;
}

function AppLayout({
  sidebarIcons,
  theme,
  Background,
  children,
  breadcrumbLabels,
  ...props
}: AppLayoutProps): JSX.Element {
  const [results, setResults] = useState<{ key: string; link: string; label: string }[]>(getResults(""));

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
    <ColorContext.Provider value={theme}>
      <Sidebar sidebarIcons={sidebarIcons}>
        <NavBar
          breadcrumbLabels={breadcrumbLabels}
          handleSearchInput={handleSearchInput}
          searchResults={results}
          user={{ icon: "" }}
        >
          {children}
          {Background}
        </NavBar>
      </Sidebar>
    </ColorContext.Provider>
  );
}

export default AppLayout;
