"use client";
import React, { useContext } from "react";
import "./Sidebar.scss";
import { usePathname } from "next/navigation";
import { ColorContext } from "../../contexts";
import SVGSidebarBackground from "../icons/elevaite/svgSidebarBackground";
import { SidebarIconObject } from "../interfaces";

interface SidebarProps {
  sidebarIcons: SidebarIconObject[];
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
        {props.sidebarIcons.map((item) => (
          <SidebarIcon key={item.link} link={item.link} description={item.description} themeType={theme.type}>
            {item.icon}
          </SidebarIcon>
        ))}
      </div>
    </div>
  );
}

export interface SidebarIconProps {
  link: string;
  description?: string;
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
        (pathname === "/" && props.link === "/") || (pathname !== "/" && props.link !== "/" && pathname.startsWith(props.link)) ? "active" : undefined,
      ].filter(Boolean).join(" ")}
      title={props.description}
      href={props.link}
    >
      {children}
    </a>
  );
}
