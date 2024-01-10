"use client";
import { ColorContext, ColorContextProvider, type ColorScheme } from "@repo/ui/contexts";
import { NavBar, Sidebar } from "@repo/ui/components";
import { useContext, useState } from "react";
import { useSession } from "next-auth/react";
import { engineerSearchHelper, userSearchHelper } from "../lib/searchHelpers";
import { logOut } from "../lib/actions";
import "./AppLayout.scss";


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
  children,
  breadcrumbLabels,
  ...props
}: AppLayoutProps): JSX.Element {
  const [results, setResults] = useState<{ key: string; link: string; label: string }[]>(getResults(""));
  const { data: session } = useSession();

  const colors = useContext(ColorContext);


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
    <ColorContextProvider 
      theme={theme}
    >
      <div className="elevaite-main-container" style={colors.getCSSVariablesColorsInjectionStyle()}>
        <NavBar
          breadcrumbLabels={breadcrumbLabels}
          handleSearchInput={handleSearchInput}
          logOut={logOut}
          searchResults={results}
          user={{ icon: session?.user?.image || "" }}
        />
        <Sidebar sidebarIcons={sidebarIcons} />
        <div className="children-container">
          {children}
        </div>
      </div>
    </ColorContextProvider>
  );
}

export default AppLayout;
