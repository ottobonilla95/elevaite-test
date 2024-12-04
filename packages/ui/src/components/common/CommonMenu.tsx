"use client";
import { useRef, useState } from "react";
import { ElevaiteIcons } from "../icons";
import { ClickOutsideDetector } from "./ClickOutsideDetector";
import { CommonButton } from "./CommonButton";
import "./CommonMenu.scss";



export interface CommonMenuItem<T> {
    label: string;
    onClick: (item: T) => void;
    tooltip?: string;
    isDisabled?: boolean;
}




interface CommonMenuProps<Τ> {
    item?: Τ;
    menu: CommonMenuItem<Τ>[];
    top?: boolean;
    left?: boolean;
    sideCover?: boolean;
    menuIcon?: React.ReactNode;
    tooltip?: string;
    labelWidth?: "short" | "medium" | "long";
}

export function CommonMenu<T>(props: CommonMenuProps<T>): JSX.Element {
    const buttonRef = useRef<HTMLButtonElement|null>(null);
    const [isOpen, setIsOpen] = useState(false);

    function toggleMenu(): void {
        setIsOpen(current => !current);
    }

    function closeMenu(): void {
        setIsOpen(false);
    }

    function handleClick(menuItem: CommonMenuItem<T>): void {
        if (props.item) menuItem.onClick(props.item);
        closeMenu();
    }

    return (
        <div className="common-menu-container">
            <CommonButton
                className="common-menu-button"
                noBackground
                passedRef={buttonRef}
                onClick={toggleMenu}
                title={props.tooltip}
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
                                    title={menuItem.tooltip}
                                    disabled={menuItem.isDisabled}
                                >
                                    <span className={["menu-label", props.labelWidth].filter(Boolean).join(" ")}>
                                        {menuItem.label}
                                    </span>
                                </CommonButton>
                            )}
                        </div>
                    </div>
                </div>
            </ClickOutsideDetector>
        </div>
    );
}