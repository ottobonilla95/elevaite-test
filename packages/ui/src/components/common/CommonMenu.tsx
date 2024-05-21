"use client";
import { useRef, useState } from "react";
import { ClickOutsideDetector, CommonButton } from ".";
import { ElevaiteIcons } from "..";
import "./CommonMenu.scss";



export interface CommonMenuItem<T> {
    label: string;
    onClick: (item: T) => void;
}




interface CommonMenuProps {
    item?: any;
    menu: CommonMenuItem<any>[];
    top?: boolean;
    left?: boolean;
    sideCover?: boolean;
    menuIcon?: React.ReactNode;
}

export function CommonMenu(props: CommonMenuProps): JSX.Element {
    const buttonRef = useRef<HTMLButtonElement|null>(null);
    const [isOpen, setIsOpen] = useState(false);

    function toggleMenu(): void {
        setIsOpen(current => !current);
    }

    function closeMenu(): void {
        setIsOpen(false);
    }

    function handleClick(menuItem: CommonMenuItem<any>): void {
        menuItem.onClick(props.item);
        closeMenu();
    }

    return (
        <div className="common-menu-container">
            <CommonButton
                className="common-menu-button"
                noBackground
                passedRef={buttonRef}
                onClick={toggleMenu}
            >
                {props.menuIcon ? props.menuIcon : <ElevaiteIcons.SVGMenuDots/>}
            </CommonButton>
            <ClickOutsideDetector onOutsideClick={closeMenu} ignoredRefs={[buttonRef]}>
                <div
                    className={[
                        "common-menu-anchor",
                        props.top ? "top" : "bottom",
                        props.left ? "left" : "right",
                        props.sideCover ? "side-cover" : undefined,
                        isOpen ? "open" : undefined,
                    ].filter(Boolean).join(" ")}
                >
                    <div className="common-menu-accordion">
                        <div className="common-menu-contents">
                            {props.menu.map(menuItem => 
                                <CommonButton
                                    key={menuItem.label}
                                    onClick={() => { handleClick(menuItem) }}
                                >
                                    {menuItem.label}
                                </CommonButton>
                            )}
                        </div>
                    </div>
                </div>
            </ClickOutsideDetector>
        </div>
    );
}