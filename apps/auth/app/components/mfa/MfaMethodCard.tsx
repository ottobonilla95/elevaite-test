"use client";
import type { JSX } from "react";
import { QrCodeIcon, SmsIcon, CheckIcon } from "../icons";

type MfaMethod = "TOTP" | "SMS";

interface MfaMethodCardProps {
  method: MfaMethod;
  title: string;
  description: string;
  isSelected: boolean;
  onClick: () => void;
  disabled?: boolean;
}

export function MfaMethodCard({
  method,
  title,
  description,
  isSelected,
  onClick,
  disabled = false,
}: MfaMethodCardProps): JSX.Element {
  const Icon = method === "TOTP" ? QrCodeIcon : SmsIcon;

  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className={`
        ui-w-full ui-bg-white ui-px-4 ui-py-6 ui-rounded-lg ui-border-2
        ui-flex ui-items-center ui-gap-3
        ui-transition-all ui-duration-200
        ${
          isSelected
            ? "ui-border-[#FF681F]"
            : "ui-border-[#E2E8ED] hover:ui-border-[#FF681F]/50"
        }
        ${disabled ? "ui-opacity-50 ui-cursor-not-allowed" : "ui-cursor-pointer"}
      `}
    >
      {/* Icon container */}
      <div className="ui-flex-shrink-0 ui-w-[46px] ui-h-[46px] ui-rounded-full ui-bg-[rgba(255,104,31,0.2)] ui-flex ui-items-center ui-justify-center ui-text-[#FF681F]">
        <Icon />
      </div>

      {/* Content */}
      <div className="ui-flex-1 ui-text-left">
        <h3 className="ui-text-[#212124] ui-font-bold ui-text-base">{title}</h3>
        <p className="ui-text-[#939393] ui-text-sm ui-font-medium ui-mt-1">
          {description}
        </p>
      </div>

      {/* Checkmark when selected */}
      {isSelected ? (
        <div className="ui-flex-shrink-0 ui-text-[#FF681F]">
          <CheckIcon />
        </div>
      ) : null}
    </button>
  );
}
