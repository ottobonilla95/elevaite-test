"use client";
import { type User } from "next-auth";
import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import React, { useEffect, useState } from "react";
import "./Navbar.scss";
import { useThemes } from "@repo/ui/contexts";
import { Breadcrumbs, CommonButton, CommonDialog, CommonMenu, ElevaiteIcons, HelpIcon, type BreadcrumbItem, type CommonMenuItem } from "@repo/ui/components";
import { logoutUser } from "../../auth";



interface NavbarMenuItem {
    label: string;
    onClick: () => void;
}

interface NavBarProps {
    breadcrumbLabels?: Record<string, { label: string; link: string }>;
    hideBreadcrumbs?: boolean;
    customBreadcrumbs?: React.ReactNode;
    user?: User;
    children?: React.ReactNode;
}

export function NavBar(props: NavBarProps): JSX.Element {
    const pathname = usePathname();
    const themesContext = useThemes();
    const [breadcrumbItems, setBreadcrumbItems] = useState<BreadcrumbItem[]>([]);
    const [isHelpActive, setIsHelpActive] = useState(false);
    const [isLogoutRequestOpen, setIsLogoutRequestOpen] = useState(false);
    const [userMenu, setUserMenu] = useState<CommonMenuItem<NavbarMenuItem>[]>([{ label: "Logout", onClick: handleLogoutRequest }]);



    useEffect(() => {
        setBreadcrumbItems(pathToBreadcrumbs(pathname));
    }, [pathname, props.breadcrumbLabels]);

    useEffect(() => {
        if (themesContext.themesList.length === 0) return;
        const themesList: CommonMenuItem<NavbarMenuItem>[] = themesContext.themesList.map(item => {
            return {
                label: item.label,
                onClick: () => { handleThemeClick(item.id) }
            }
        });
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

    function logout(): Promise<void> {
        return logoutUser(props.user?.accessToken ?? "");
    }

    async function handleLogout(): Promise<void> {
        await logout();
    }

    function pathToBreadcrumbs(path: string): BreadcrumbItem[] {
        if (!props.breadcrumbLabels) return [];
        if (pathname === "/") return [props.breadcrumbLabels.home];
        const runningPath = path.split("/").filter((str) => str !== "");
        return runningPath.map((str, index) => {
            const breadcrumb: { label: string; link: string } | undefined = props.breadcrumbLabels?.[str];
            return {
                label: breadcrumb ? breadcrumb.label : str,
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
                    onCancel={() => { setIsLogoutRequestOpen(false); }}
                />
            }

            <div className="navbar-holder">

                <div className="navbar-left">
                    <Link href="/">
                        <ElevaiteIcons.SVGNavbarLogo />
                    </Link>
                    {props.hideBreadcrumbs ? undefined :
                        props.customBreadcrumbs ? props.customBreadcrumbs :
                            <Breadcrumbs items={breadcrumbItems} />}
                </div>

                <div className="navbar-right">



                    <CommonButton
                        className={["help-button", isHelpActive ? "active" : undefined].filter(Boolean).join(" ")}
                        onClick={handleHelpClick}
                    >
                        <HelpIcon />
                    </CommonButton>

                    <div className="separator" />

                    {props.user?.name}

                    <CommonMenu<NavbarMenuItem>
                        item={undefined}
                        menu={userMenu}
                        left
                        sideCover
                        menuIcon={
                            <div className="icon-container">
                                {!props.user?.image ? <ElevaiteIcons.SVGMenuDots /> :
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

