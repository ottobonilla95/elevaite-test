"use client";
import { ColorContext, ColorScheme, ElevaiteIcons, NavBar, Sidebar, SidebarIconProps } from "@elevaite/ui";
import { useState } from "react";
import { engineerSearchHelper, userSearchHelper } from "../lib/searchHelpers";

interface AppLayoutProps {
  sidebarIcons: SidebarIconProps[];
  theme: ColorScheme;
  layout: "user" | "engineer";
  Background?: React.ReactNode;
  children: React.ReactNode;
  breadcrumbLabels: { [key: string]: { label: string; link: string } };
}

function AppLayout({ sidebarIcons, theme, Background, children, breadcrumbLabels, ...props }: AppLayoutProps) {
  const [results, setResults] = useState<{ key: string; link: string; label: string }[]>(getResults(""));

  function getResults(term: string) {
    switch (props.layout) {
      case "user": {
        return userSearchHelper(term);
      }
      case "engineer": {
        return engineerSearchHelper(term);
      }
      default: {
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
      <Sidebar Logo={<ElevaiteIcons.Logo />} sidebarIcons={sidebarIcons}>
        <NavBar
          breadcrumbLabels={breadcrumbLabels}
          user={{ icon: "" }}
          handleSearchInput={handleSearchInput}
          searchResults={results}
        >
          {children}
          {Background}
        </NavBar>
      </Sidebar>
    </ColorContext.Provider>
  );
}

export default AppLayout;
