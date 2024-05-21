"use client";
import { User } from "next-auth";
import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import React, { useEffect, useState } from "react";
import { useThemes } from "../../contexts/ColorContext";
import { CommonButton, CommonDialog, CommonMenu, CommonMenuItem } from "../common";
import { ElevaiteIcons } from "../icons";
import SVGHelp from "../icons/svgHelp";
import { Searchbar } from "../search/Searchbar";
import type { BreadcrumbItem } from "./Breadcrumbs";
import { Breadcrumbs } from "./Breadcrumbs";
import "./Navbar.scss";



interface NavBarProps {
  breadcrumbLabels: Record<string, { label: string; link: string }>;
  user?: User;
  handleSearchInput: (term: string) => void;
  searchResults: { key: string; link: string; label: string }[];
  logOut: () => void;
  children?: React.ReactNode;
}

export function NavBar(props: NavBarProps): JSX.Element {
  const pathname = usePathname();
  const themesContext = useThemes();
  const [breadcrumbItems, setBreadcrumbItems] = useState<BreadcrumbItem[]>([]);
  const [isHelpActive, setIsHelpActive] = useState(false);
  const [isLogoutRequestOpen, setIsLogoutRequestOpen] = useState(false);
  const [userMenu, setUserMenu] = useState<CommonMenuItem<undefined>[]>([{ label: "Logout", onClick: () => { handleLogoutRequest(); } }]);



  useEffect(() => {
    setBreadcrumbItems(pathToBreadcrumbs(pathname));
  }, [pathname, props.breadcrumbLabels]);

  useEffect(() => {
    if (themesContext.themesList.length === 0) return;
    const themesList: CommonMenuItem<undefined>[] = themesContext.themesList.map(item => { return {
      label: item.label,
      onClick: () => { handleThemeClick(item.id) }
    }});
    themesList.push({ label: "Logout", onClick: () => { handleLogoutRequest(); } });
    setUserMenu(themesList);
  }, [themesContext.themesList]);


  function handleThemeClick(themeId: string): void {
    themesContext.changeTheme(themeId);
  }

  function handleLogoutRequest(): void {
    setIsLogoutRequestOpen(true);
  }

  function handleHelpClick(): void {
    setIsHelpActive(!isHelpActive);
  }

  function handleLogout(): void {
    props.logOut();
  }
  
  function pathToBreadcrumbs(path: string): BreadcrumbItem[] {
    if (pathname === "/") return [props.breadcrumbLabels.home];
    const runningPath = path.split("/").filter((str) => str !== "");
    return runningPath.map((str, index) => {
      const breadcrumb: { label: string; link: string } | undefined = props.breadcrumbLabels[str];
      return {
        // eslint-disable-next-line @typescript-eslint/no-unnecessary-condition -- Could be undefined
        label: breadcrumb ? breadcrumb.label : str,
        // eslint-disable-next-line @typescript-eslint/no-unnecessary-condition -- Could be undefined
        link: index < runningPath.length - 1 && breadcrumb ? breadcrumb.link : "",
      };
    });
  }



  return (
    <div className="navbar-container">

      {!isLogoutRequestOpen ? undefined :
        <CommonDialog
          title="Are you sure you want to log out?"
          onConfirm={handleLogout}
          onCancel={() => setIsLogoutRequestOpen(false)}
        />
      }

      <div className="navbar-holder">

        <div className="navbar-left">
          <Link href="/">
            <ElevaiteIcons.SVGNavbarLogo />
          </Link>
          <Breadcrumbs items={breadcrumbItems} />
        </div>

        <div className="navbar-right">

          <Searchbar
            handleInput={props.handleSearchInput}
            isJump
            results={props.searchResults}
            resultsTopOffset="70px"
          />

          <CommonButton
            className={["help-button", isHelpActive ? "active" : undefined].filter(Boolean).join(" ")}
            onClick={handleHelpClick}
          >
            <SVGHelp/>
          </CommonButton>

          <div className="separator"/>

          {props.user?.name}

          <CommonMenu
            item={undefined}
            menu={userMenu}
            left
            sideCover
            menuIcon={
              <div className="icon-container">
              {!props.user?.image ? <ElevaiteIcons.SVGMenuDots/> :
                <Image alt="User Image" height={40} width={40} src={props.user.image} />
              }
              </div>
            }
          />

        </div>
      </div>
      {props.children}
    </div>
  );
}

