"use client";
import Link from "next/link";
import React, { useState } from "react";
import "./Navbar.css";
import { Breadcrumbs, BreadcrumbItem } from "./Breadcrumbs";
import Searchbar from "../search/Searchbar";

interface NavBarProps {
  breadcrumbItems: BreadcrumbItem[];
  user: { icon: string };
  children?: React.ReactNode;
}

export function NavBar({ ...props }: NavBarProps) {
  const [btnPressed, setBtnpressed] = useState(false);
  return (
    <div className="layoutL2">
      <div className="navbarHolder">
        <Breadcrumbs items={props.breadcrumbItems} />
        <div className="searchAndUser">
          <Searchbar />
          <button
            className="help"
            onClick={() => {
              setBtnpressed(!btnPressed);
            }}
            style={{ background: btnPressed ? "#363636" : "" }}
          >
            <svg
              width="20"
              height="20"
              viewBox="0 0 20 20"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
              style={{ stroke: btnPressed ? "#E75F33" : "#939393" }}
            >
              <g clip-path="url(#clip0_910_5173)">
                <path
                  d="M7.57508 7.49999C7.771 6.94305 8.15771 6.47341 8.66671 6.17427C9.17571 5.87512 9.77416 5.76577 10.3561 5.86558C10.938 5.96539 11.4658 6.26793 11.846 6.7196C12.2262 7.17127 12.4343 7.74293 12.4334 8.33332C12.4334 9.99999 9.93342 10.8333 9.93342 10.8333M10.0001 14.1667H10.0084M18.3334 9.99999C18.3334 14.6024 14.6025 18.3333 10.0001 18.3333C5.39771 18.3333 1.66675 14.6024 1.66675 9.99999C1.66675 5.39762 5.39771 1.66666 10.0001 1.66666C14.6025 1.66666 18.3334 5.39762 18.3334 9.99999Z"
                  stroke="current"
                  stroke-width="2"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                />
              </g>
              <defs>
                <clipPath id="clip0_910_5173">
                  <rect width="20" height="20" fill="currentColor" stroke="currentColor" />
                </clipPath>
              </defs>
            </svg>
          </button>
          <line className="line" />
        </div>
      </div>
      {props.children}
    </div>
  );
}

export default NavBar;
