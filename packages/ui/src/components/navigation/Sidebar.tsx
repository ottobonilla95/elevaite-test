import React, { ComponentType, SVGProps } from "react";
import "./Sidebar.css";

interface SidebarProps {
  sidebarIcons: SidebarIconProps[];
  Logo: ComponentType<SVGProps<SVGSVGElement>>;
  children?: React.ReactNode;
}

export function Sidebar({ Logo, ...props }: SidebarProps) {
  return (
    <div className="layout">
      <div className="sidebarContainer">
        <div className="logoContainer">
          <Logo className="sidebarLogo" width={56} height={56} color="#E75F33" />
        </div>
        <div className="sidebarNav">
          {props.sidebarIcons.map((icon, index) => (
            <React.Fragment>
              <button className={"sidebarNavBtn" + (icon.selected ? " slc" : "")}>
                <icon.Icon color={icon.selected ? "#E75F33" : "#fff"} />
              </button>
            </React.Fragment>
          ))}
        </div>
      </div>
      {props.children}
    </div>
  );
}

export default Sidebar;

interface SidebarIconProps {
  Icon: ComponentType<SVGProps<SVGSVGElement>>;
  linkLocations: string;
  selected: boolean;
}

function SidebarIcon({ Icon, ...props }: SidebarIconProps) {
  function onClick() {}

  return <div></div>;
}
