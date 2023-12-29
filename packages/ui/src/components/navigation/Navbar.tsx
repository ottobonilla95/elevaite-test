"use client";
import React, { useContext, useEffect, useState } from "react";
import "./Navbar.css";
import { usePathname } from "next/navigation";
import Image from "next/image";
import { Searchbar } from "../search/Searchbar";
import { ColorContext } from "../../contexts";
import type { BreadcrumbItem } from "./Breadcrumbs";
import { Breadcrumbs } from "./Breadcrumbs";

interface NavBarProps {
  breadcrumbLabels: Record<string, { label: string; link: string }>;
  user?: { icon?: string; fullName?: string };

  children?: React.ReactNode;
  handleSearchInput: (term: string) => void;
  searchResults: { key: string; link: string; label: string }[];
  logOut: () => Promise<"Invalid credentials." | "Something went wrong." | undefined>;
}

export function NavBar({ ...props }: NavBarProps): JSX.Element {
  const [btnPressed, setBtnPressed] = useState(false);
  const [breadcrumbItems, setBreadcrumbItems] = useState<BreadcrumbItem[]>([]);
  const [hover, setHover] = useState(false);
  const pathname = usePathname();
  useEffect(() => {
    function pathToBreadcrumbs(path: string): BreadcrumbItem[] {
      if (pathname === "/") return [props.breadcrumbLabels.home];
      return path
        .split("/")
        .filter((str) => str !== "")
        .map((str) => {
          const breadcrumb: { label: string; link: string } | undefined = props.breadcrumbLabels[str];
          return {
            // eslint-disable-next-line @typescript-eslint/no-unnecessary-condition -- Could be undefined
            label: breadcrumb ? breadcrumb.label : str,
            // eslint-disable-next-line @typescript-eslint/no-unnecessary-condition -- Could be undefined
            link: breadcrumb ? breadcrumb.link : "",
          };
        });
    }
    setBreadcrumbItems(pathToBreadcrumbs(pathname));
  }, [pathname, props.breadcrumbLabels]);
  const colors = useContext(ColorContext);

  async function handleLogout(): Promise<void> {
    await props.logOut();
  }

  return (
    <div className="layoutL2">
      <div className="navbarHolder" style={{ borderBottomColor: colors.borderColor, background: colors.primary }}>
        <Breadcrumbs items={breadcrumbItems} />
        <div className="searchAndUser">
          <Searchbar
            handleInput={props.handleSearchInput}
            isJump
            results={props.searchResults}
            resultsTopOffset="70px"
            width="280px"
          />
          <button
            className="help"
            onClick={() => {
              setBtnPressed(!btnPressed);
            }}
            onFocus={() => {
              setHover(true);
            }}
            onMouseEnter={() => {
              setHover(true);
            }}
            onMouseLeave={() => {
              setHover(false);
            }}
            style={{ background: btnPressed || hover ? colors.hoverColor : "", borderColor: colors.borderColor }}
            type="button"
          >
            <svg
              fill="none"
              height="20"
              style={{ stroke: btnPressed ? colors.highlight : colors.icon }}
              viewBox="0 0 20 20"
              width="20"
              xmlns="http://www.w3.org/2000/svg"
            >
              <g clipPath="url(#clip0_910_5173)">
                <path
                  d="M7.57508 7.49999C7.771 6.94305 8.15771 6.47341 8.66671 6.17427C9.17571 5.87512 9.77416 5.76577 10.3561 5.86558C10.938 5.96539 11.4658 6.26793 11.846 6.7196C12.2262 7.17127 12.4343 7.74293 12.4334 8.33332C12.4334 9.99999 9.93342 10.8333 9.93342 10.8333M10.0001 14.1667H10.0084M18.3334 9.99999C18.3334 14.6024 14.6025 18.3333 10.0001 18.3333C5.39771 18.3333 1.66675 14.6024 1.66675 9.99999C1.66675 5.39762 5.39771 1.66666 10.0001 1.66666C14.6025 1.66666 18.3334 5.39762 18.3334 9.99999Z"
                  stroke="current"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="2"
                />
              </g>
              <defs>
                <clipPath id="clip0_910_5173">
                  <rect fill="currentColor" height="20" stroke="currentColor" width="20" />
                </clipPath>
              </defs>
            </svg>
          </button>
          <line className="line" style={{ background: colors.borderColor }} />
          {props.user?.fullName}
          <button
            onClick={() => {
              handleLogout().catch((e) => {
                // eslint-disable-next-line no-console -- Temporary until better logging
                console.log(e);
              });
            }}
            type="button"
          >
            {props.user?.icon ? <Image alt="User Image" height={40} src={props.user.icon} width={40} /> : "Logout"}
          </button>
        </div>
      </div>
      {props.children}
    </div>
  );
}

export default NavBar;
