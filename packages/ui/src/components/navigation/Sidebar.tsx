"use client";
import React, { useContext } from "react";
import "./Sidebar.css";
import { usePathname } from "next/navigation";
import Link from "next/link";
import { ColorContext } from "../../ColorContext";

interface SidebarProps {
  sidebarIcons: SidebarIconProps[];
  Logo: React.ReactNode;
  children?: React.ReactNode;
}

export function Sidebar({ Logo, ...props }: SidebarProps) {
  const colors = useContext(ColorContext);
  return (
    <div className="layout">
      <div className="sidebarContainer" style={{ borderRightColor: colors.borderColor, background: colors.primary }}>
        <div className="logoContainer">
          <div className="logo">{Logo}</div>
        </div>
        <div className="sidebarNav">
          {props.sidebarIcons.map((icon, index) => (
            <SidebarIcon Icon={icon.Icon} linkLocation={icon.linkLocation} key={icon.linkLocation} />
          ))}
        </div>
      </div>
      {props.children}
    </div>
  );
}

export interface SidebarIconProps {
  Icon: React.ReactNode;
  linkLocation: string;
}

function SidebarIcon({ Icon, ...props }: SidebarIconProps) {
  const pathname = usePathname();
  const [hover, setHover] = React.useState(false);
  const colors = useContext(ColorContext);

  return (
    <React.Fragment>
      <button
        className={"sidebarNavBtn" + (pathname.startsWith(props.linkLocation) ? "_slc" : "")}
        // onClick={() => {
        //   push(props.linkLocation);
        // }}
        style={{
          color: pathname.startsWith(props.linkLocation) ? colors.highlight : colors.icon,
          background: pathname.startsWith(props.linkLocation) || hover ? colors.secondary : colors.primary,
          borderColor: pathname.startsWith(props.linkLocation) ? colors.iconBorder : colors.primary,
        }}
        onMouseEnter={() => setHover(true)}
        onMouseLeave={() => setHover(false)}
      >
        {" "}
        <Link href={props.linkLocation}>{Icon}</Link>
      </button>
    </React.Fragment>
  );
}
