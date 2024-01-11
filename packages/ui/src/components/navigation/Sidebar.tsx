"use client";
import React, { useContext } from "react";
import "./Sidebar.scss";
import { usePathname } from "next/navigation";
import { ColorContext } from "../../contexts";
import SVGSidebarBackground from "../icons/elevaite/svgSidebarBackground";

interface SidebarProps {
  sidebarIcons: {
    linkLocation: string;
    Icon: React.ReactNode;
  }[];
}

export function Sidebar({ ...props }: SidebarProps): JSX.Element {
  const theme = useContext(ColorContext);
  return (
    <div className={[
      "sidebar-container",
      theme.type
      ].join(" ")}
    >
      <div className="sidebar-nav">
        <SVGSidebarBackground className="sidebar-backdrop"/>
        {props.sidebarIcons.map((icon) => (
          <SidebarIcon key={icon.linkLocation} linkLocation={icon.linkLocation} themeType={theme.type}>
            {icon.Icon}
          </SidebarIcon>
        ))}
      </div>
    </div>
  );
}

export interface SidebarIconProps {
  linkLocation: string;
  children?: React.ReactNode;
  themeType?: "dark" | "light";
}

function SidebarIcon({ children, ...props }: SidebarIconProps): JSX.Element {
  const pathname = usePathname();

  return (
    <a
      className={[
        "sidebar-nav-button",
        props.themeType,
        pathname.startsWith(props.linkLocation) ? "active" : undefined,
      ].filter(Boolean).join(" ")}
      href={props.linkLocation}
    >
      {children}
    </a>
  );
}
