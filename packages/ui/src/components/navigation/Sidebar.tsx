"use client";
import React, { ComponentType, SVGProps, useEffect } from "react";
import "./Sidebar.css";
import { useRouter, usePathname } from "next/navigation";

interface SidebarProps {
  sidebarIcons: SidebarIconProps[];
  Logo: React.ReactNode;
  children?: React.ReactNode;
}

export function Sidebar({ Logo, ...props }: SidebarProps) {
  return (
    <div className="layout">
      <div className="sidebarContainer">
        <div className="logoContainer">
          <div className="logo">{Logo}</div>
        </div>
        <div className="sidebarNav">
          {props.sidebarIcons.map((icon, index) => (
            <SidebarIcon Icon={icon.Icon} linkLocation={icon.linkLocation} />
          ))}
        </div>
      </div>
      {props.children}
    </div>
  );
}

export default Sidebar;

interface SidebarIconProps {
  Icon: React.ReactNode;
  linkLocation: string;
}

function SidebarIcon({ Icon, ...props }: SidebarIconProps) {
  const { push } = useRouter();
  const pathname = usePathname();

  return (
    <React.Fragment key={props.linkLocation}>
      <button
        className={"sidebarNavBtn" + (pathname.startsWith(props.linkLocation) ? "_slc" : "")}
        onClick={() => {
          push(props.linkLocation);
        }}
      >
        {Icon}
      </button>
    </React.Fragment>
  );
}
