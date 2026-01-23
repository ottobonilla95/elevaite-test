"use client";
import type { JSX } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useThemes } from "../../contexts";
import SVGSidebarBackground from "../icons/elevaite/svgSidebarBackground";
import { SidebarIconObject } from "../interfaces";
import "./Sidebar.scss";

interface SidebarProps {
  sidebarIcons: SidebarIconObject[];
}

export function Sidebar({ ...props }: SidebarProps): JSX.Element {
  const theme = useThemes();
  return (
    <div className={[
      "sidebar-container",
      "dark", // theme.type
      ].join(" ")}
    >
      <div className="sidebar-nav">
        <SVGSidebarBackground className="sidebar-backdrop"/>
        {props.sidebarIcons.map((item) => (
          <SidebarIcon key={item.link} link={item.link} description={item.description} themeType={"dark"}>
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
    <Link
      className={[
        "sidebar-nav-button",
        props.themeType,
        (pathname === "/" && props.link === "/") || (pathname !== "/" && props.link !== "/" && pathname.startsWith(props.link)) ? "active" : undefined,
      ].filter(Boolean).join(" ")}
      title={props.description}
      href={props.link}
    >
      {children}
    </Link>
  );
}
