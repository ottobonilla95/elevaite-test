"use client";
import type { JSX } from "react";
import { useRef, useState } from "react";
import { cls } from "../../helpers";
import { useFloatingElement } from "../../hooks/useFloatingElement";
import "./CommonTooltip.scss";

export interface CommonTooltipProps {
  tooltip: React.ReactNode;
  children: React.ReactNode;
  placement?: "top" | "bottom" | "left" | "right";
  delay?: number;
  isOpen?: boolean;
  className?: string;
  anchorClassName?: string;
  disabled?: boolean;
}

export function CommonTooltip(props: CommonTooltipProps): JSX.Element {
  const {
    tooltip,
    children,
    placement = "top",
    delay = 300,
    isOpen: controlledIsOpen,
    className,
    anchorClassName,
    disabled,
  } = props;
  const [internalIsOpen, setInternalIsOpen] = useState(false);
  const isControlled = controlledIsOpen !== undefined;
  const isOpen = isControlled ? controlledIsOpen : internalIsOpen;
  const isEffectivelyOpen = disabled ? false : isOpen;
  const timeoutRef = useRef<NodeJS.Timeout>(undefined);

  const { anchorRef, floatingRef, position, renderPortal } = useFloatingElement(
    {
      isOpen: isEffectivelyOpen,
      placement,
      offset: 8,
      onClose: () => {
        if (!isControlled) {
          setInternalIsOpen(false);
        }
      },
    },
  );

  function handleMouseEnter(): void {
    if (disabled) return;
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }

    timeoutRef.current = setTimeout(() => {
      if (!isControlled) {
        setInternalIsOpen(true);
      }
    }, delay);
  }

  function handleMouseLeave(): void {
    if (disabled) return;
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }

    if (!isControlled) {
      setInternalIsOpen(false);
    }
  }

  return (
    <>
      {disabled ? (
        children
      ) : (
        <>
          <div
            ref={anchorRef as React.RefObject<HTMLDivElement>}
            className={cls("common-tooltip-anchor", anchorClassName)}
            onMouseEnter={handleMouseEnter}
            onMouseLeave={handleMouseLeave}
          >
            {children}
          </div>
          {renderPortal(
            <div
              ref={floatingRef as React.RefObject<HTMLDivElement>}
              className={cls(
                "common-tooltip-floating-container",
                isEffectivelyOpen ? "open" : undefined,
                className,
              )}
              style={{
                position: "fixed",
                ...position,
                pointerEvents: "none",
              }}
            >
              <div className="common-tooltip-content">{tooltip}</div>
            </div>,
          )}
        </>
      )}
    </>
  );
}
