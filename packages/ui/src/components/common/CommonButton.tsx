import React, { type ButtonHTMLAttributes, type MutableRefObject } from "react";
import "./CommonButton.scss";

export interface CommonButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  theme?: "light" | "dark";
  noBackground?: boolean;
  overrideClass?: boolean;
  passedRef?: MutableRefObject<HTMLButtonElement | null>;
  onMiddleClick?: () => void;
  children: React.ReactNode;
}

export function CommonButton({
  className,
  overrideClass,
  noBackground,
  theme,
  passedRef,
  onMiddleClick,
  type = "button",
  ...props
}: CommonButtonProps): React.ReactElement<CommonButtonProps> {
  function check(event: React.MouseEvent<HTMLButtonElement>): void {
    if (event.button === 1) {
      if (onMiddleClick) onMiddleClick();
    }
  }

  return (
    <button
      ref={passedRef}
      type={type}
      {...props}
      className={[
        "common-button",
        overrideClass ? undefined : "not-overriden",
        className,
        noBackground ? "no-background" : undefined,
        theme,
      ]
        .filter(Boolean)
        .join(" ")}
      onMouseUp={check}
    >
      {props.children}
    </button>
  );
}
