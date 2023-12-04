"use client";
import React, { useContext, useEffect, useState } from "react";
import "./Navbar.css";
import { Breadcrumbs, BreadcrumbItem } from "./Breadcrumbs";
import { Searchbar } from "../search/Searchbar";
import { usePathname } from "next/navigation";
import { ColorContext } from "../../ColorContext";

interface NavBarProps {
  breadcrumbLabels: { [key: string]: { label: string; link: string } };
  user: { icon: string };
  children?: React.ReactNode;
  handleSearchInput: (term: string) => void;
  searchResults: { key: string; link: string; label: string }[];
}

export function NavBar({ ...props }: NavBarProps) {
  const [btnPressed, setBtnpressed] = useState(false);
  const [breadcrumbItems, setBreadcrumbItems] = useState<BreadcrumbItem[]>([]);
  const [hover, setHover] = React.useState(false);
  const pathname = usePathname();
  useEffect(() => {
    setBreadcrumbItems(pathToBreadcrumbs(pathname));
  }, []);
  const colors = useContext(ColorContext);

  function pathToBreadcrumbs(path: string): BreadcrumbItem[] {
    return path
      .split("/")
      .filter((str) => str != "")
      .map((str) => {
        return {
          label: props.breadcrumbLabels[str] ? props.breadcrumbLabels[str].label : str,
          link: props.breadcrumbLabels[str]?.link,
        };
      });
  }

  return (
    <div className="layoutL2">
      <div className="navbarHolder" style={{ borderBottomColor: colors.borderColor, background: colors.primary }}>
        <Breadcrumbs items={breadcrumbItems} />
        <div className="searchAndUser">
          <Searchbar handleInput={props.handleSearchInput} results={props.searchResults} />
          <button
            className="help"
            onClick={() => {
              setBtnpressed(!btnPressed);
            }}
            style={{ background: btnPressed || hover ? colors.hoverColor : "", borderColor: colors.borderColor }}
            onMouseEnter={() => setHover(true)}
            onFocus={() => setHover(true)}
            onMouseLeave={() => setHover(false)}
          >
            <svg
              width="20"
              height="20"
              viewBox="0 0 20 20"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
              style={{ stroke: btnPressed ? colors.highlight : colors.icon }}
            >
              <g clipPath="url(#clip0_910_5173)">
                <path
                  d="M7.57508 7.49999C7.771 6.94305 8.15771 6.47341 8.66671 6.17427C9.17571 5.87512 9.77416 5.76577 10.3561 5.86558C10.938 5.96539 11.4658 6.26793 11.846 6.7196C12.2262 7.17127 12.4343 7.74293 12.4334 8.33332C12.4334 9.99999 9.93342 10.8333 9.93342 10.8333M10.0001 14.1667H10.0084M18.3334 9.99999C18.3334 14.6024 14.6025 18.3333 10.0001 18.3333C5.39771 18.3333 1.66675 14.6024 1.66675 9.99999C1.66675 5.39762 5.39771 1.66666 10.0001 1.66666C14.6025 1.66666 18.3334 5.39762 18.3334 9.99999Z"
                  stroke="current"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </g>
              <defs>
                <clipPath id="clip0_910_5173">
                  <rect width="20" height="20" fill="currentColor" stroke="currentColor" />
                </clipPath>
              </defs>
            </svg>
          </button>
          <line className="line" style={{ background: colors.borderColor }} />
        </div>
      </div>
      {props.children}
    </div>
  );
}

export default NavBar;
