"use client";
import React, { useContext, useState } from "react";
import "./Sidebar.css";
import { usePathname } from "next/navigation";
import Link from "next/link";
import { ColorContext } from "../../contexts";
import ElevaiteLogo from "../icons/elevaite/logo";

interface SidebarProps {
  sidebarIcons: {
    linkLocation: string;
    Icon: React.ReactNode;
  }[];
  children?: React.ReactNode;
}

export function Sidebar({ ...props }: SidebarProps): JSX.Element {
  const colors = useContext(ColorContext);
  return (
    <>
      <div className="sidebarContainer" style={{ borderRightColor: colors.borderColor, background: colors.primary }}>
        <Link className="logoContainer" href="/">
          <ElevaiteLogo />
        </Link>
        <div className="sidebarNav">
          {props.sidebarIcons.map((icon) => (
            <SidebarIcon key={icon.linkLocation} linkLocation={icon.linkLocation}>
              {icon.Icon}
            </SidebarIcon>
          ))}
        </div>
      </div>
      {props.children}
    </>
  );
}

export interface SidebarIconProps {
  linkLocation: string;
  children?: React.ReactNode;
}

function SidebarIcon({ children, ...props }: SidebarIconProps): JSX.Element {
  const pathname = usePathname();
  const [hover, setHover] = useState(false);
  const colors = useContext(ColorContext);

  return (
    <a
      className={`sidebarNavBtn${pathname.startsWith(props.linkLocation) ? "_slc" : ""}`}
      href={props.linkLocation}
      onMouseEnter={() => {
        setHover(true);
      }}
      onMouseLeave={() => {
        setHover(false);
      }}
      style={{
        color: pathname.startsWith(props.linkLocation) ? colors.highlight : colors.icon,
        background: pathname.startsWith(props.linkLocation) || hover ? colors.secondary : colors.primary,
        borderColor: pathname.startsWith(props.linkLocation) ? colors.iconBorder : colors.primary,
      }}
    >
      {children}
    </a>
  );
}
