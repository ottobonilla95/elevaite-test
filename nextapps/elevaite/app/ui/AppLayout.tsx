"use client";
import { ColorContext, ColorScheme, ElevaiteIcons, NavBar, Sidebar, SidebarIconProps } from "@elevaite/ui";

interface AppLayoutProps {
  sidebarIcons: SidebarIconProps[];
  theme: ColorScheme;
  Background?: React.ReactNode;
  children: React.ReactNode;
  breadcrumbLabels: { [key: string]: { label: string; link: string } };
}

function AppLayout({ sidebarIcons, theme, Background, children, breadcrumbLabels, ...props }: AppLayoutProps) {
  return (
    <ColorContext.Provider value={theme}>
      <Sidebar Logo={<ElevaiteIcons.Logo />} sidebarIcons={sidebarIcons}>
        <NavBar breadcrumbLabels={breadcrumbLabels} user={{ icon: "" }}>
          {Background}
          {children}
        </NavBar>
      </Sidebar>
    </ColorContext.Provider>
  );
}

export default AppLayout;
