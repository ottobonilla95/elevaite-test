"use client";
import type { JSX } from "react";
import { useRef, useState } from "react";
import { cls } from "../../helpers";
import { useFloatingElement } from "../../hooks/useFloatingElement";
import { ElevaiteIcons } from "../icons";
import { ClickOutsideDetector } from "./ClickOutsideDetector";
import { CommonButton } from "./CommonButton";
import "./CommonMenu.scss";
import { CommonTooltip, type CommonTooltipProps } from "./CommonTooltip";

export type CommonMenuItem<T = undefined> =
  | {
      label: string;
      onClick: T extends undefined ? () => void : (item: T) => void;
      icon?: React.ReactNode;
      tooltip?: string | Omit<CommonTooltipProps, "children">;
      isDisabled?: boolean;
      isCategoryLabel?: false | undefined;
      suffix?: React.ReactNode;
    }
  | {
      label: string;
      isCategoryLabel: true;
      icon?: React.ReactNode;
      tooltip?: string | Omit<CommonTooltipProps, "children">;
      suffix?: React.ReactNode;
    };

interface CommonMenuProps<Τ> {
  item?: Τ;
  menu: CommonMenuItem<Τ>[];
  top?: boolean;
  left?: boolean;
  sideCover?: boolean;
  menuIcon?: React.ReactNode;
  tooltip?: string | Omit<CommonTooltipProps, "children">;
  labelWidth?: "short" | "medium" | "long";
  useAlternativeClickOutsideDetector?: boolean;
  className?: string;
  usePortal?: boolean;
  menuClassName?: string;
}

export function CommonMenu<T>(props: CommonMenuProps<T>): JSX.Element {
  const buttonRef = useRef<HTMLButtonElement | null>(null);
  const [isOpen, setIsOpen] = useState(false);
  const placement = props.top ? "top" : "bottom";
  const align = props.left ? "right" : "left";

  const { anchorRef, floatingRef, position, renderPortal } = useFloatingElement(
    {
      isOpen: isOpen && (props.usePortal ?? false),
      placement,
      align,
      offset: 5,
      onClose: () => {
        setIsOpen(false);
      },
    },
  );

  function toggleMenu(): void {
    setIsOpen((current) => !current);
  }

  function closeMenu(): void {
    setIsOpen(false);
  }

  function handleClick(menuItem: CommonMenuItem<T>): void {
    if (!menuItem.isCategoryLabel) {
      menuItem.onClick(props.item as T);
    }
    closeMenu();
  }

  const floatingContent = (
    <div
      ref={floatingRef as React.RefObject<HTMLDivElement>}
      className={cls(
        props.menuClassName,
        props.usePortal ? "common-menu-floating" : "common-menu-anchor",
        props.top && !props.usePortal ? "top" : undefined,
        !props.top && !props.usePortal ? "bottom" : undefined,
        props.left && !props.usePortal ? "left" : undefined,
        !props.left && !props.usePortal ? "right" : undefined,
        props.sideCover && !props.usePortal ? "side-cover" : undefined,
        isOpen ? "open" : undefined,
      )}
      style={
        props.usePortal
          ? {
              position: "fixed",
              ...position,
              pointerEvents: isOpen ? "all" : "none",
            }
          : undefined
      }
    >
      <div className="common-menu-accordion">
        <div className="common-menu-contents">
          {props.menu.map((menuItem) => {
            if (menuItem.isCategoryLabel) {
              return (
                <div
                  key={menuItem.label}
                  className="common-menu-item-category-label"
                >
                  {menuItem.icon ? menuItem.icon : undefined}
                  <span className={cls("menu-label", props.labelWidth)}>
                    {menuItem.label}
                  </span>
                  {menuItem.suffix}
                </div>
              );
            }

            const isStringItemTooltip = typeof menuItem.tooltip === "string";
            const itemTooltipProps: Omit<CommonTooltipProps, "children"> =
              isStringItemTooltip
                ? { tooltip: menuItem.tooltip as string, disabled: true }
                : {
                    ...(menuItem.tooltip as Omit<
                      CommonTooltipProps,
                      "children"
                    >),
                    disabled: !menuItem.tooltip,
                  };

            return (
              <CommonTooltip key={menuItem.label} {...itemTooltipProps}>
                <CommonButton
                  className="common-menu-item-button"
                  onClick={() => {
                    handleClick(menuItem);
                  }}
                  title={
                    isStringItemTooltip
                      ? (menuItem.tooltip as string)
                      : undefined
                  }
                  disabled={menuItem.isDisabled}
                >
                  {menuItem.icon ?? null}
                  <span className={cls("menu-label", props.labelWidth)}>
                    {menuItem.label}
                  </span>
                  {menuItem.suffix}
                </CommonButton>
              </CommonTooltip>
            );
          })}
        </div>
      </div>
    </div>
  );

  const isStringTooltip = typeof props.tooltip === "string";
  const tooltipProps: Omit<CommonTooltipProps, "children"> = isStringTooltip
    ? { tooltip: props.tooltip as string, disabled: true }
    : {
        ...(props.tooltip as Omit<CommonTooltipProps, "children">),
        disabled: !props.tooltip,
      };

  return (
    <div
      className={cls("common-menu-container", props.className)}
      ref={
        props.usePortal
          ? (anchorRef as React.RefObject<HTMLDivElement>)
          : undefined
      }
    >
      <CommonTooltip {...tooltipProps}>
        <CommonButton
          className="common-menu-button"
          noBackground
          passedRef={buttonRef}
          onClick={toggleMenu}
          title={isStringTooltip ? (props.tooltip as string) : undefined}
        >
          {props.menuIcon ? props.menuIcon : <ElevaiteIcons.SVGMenuDots />}
        </CommonButton>
      </CommonTooltip>
      <ClickOutsideDetector
        onOutsideClick={closeMenu}
        ignoredRefs={[
          buttonRef as unknown as React.MutableRefObject<HTMLElement | null>,
          floatingRef as unknown as React.MutableRefObject<HTMLElement | null>,
        ]}
        useAltHandling={props.useAlternativeClickOutsideDetector}
      >
        {props.usePortal ? renderPortal(floatingContent) : floatingContent}
      </ClickOutsideDetector>
    </div>
  );
}
