"use client";
import type { JSX } from "react";

type MfaMethod = "TOTP" | "SMS";

interface MfaMethodCardProps {
  method: MfaMethod;
  title: string;
  description: string;
  isSelected: boolean;
  onClick: () => void;
  disabled?: boolean;
}

function QrCodeIcon(): JSX.Element {
  return (
    <svg
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <rect x="3" y="3" width="7" height="7" />
      <rect x="14" y="3" width="7" height="7" />
      <rect x="14" y="14" width="7" height="7" />
      <rect x="3" y="14" width="7" height="7" />
    </svg>
  );
}

function SmsIcon(): JSX.Element {
  return (
    <svg
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
      <line x1="8" y1="9" x2="16" y2="9" />
      <line x1="8" y1="13" x2="14" y2="13" />
    </svg>
  );
}

function CheckIcon(): JSX.Element {
  return (
    <svg
      width="20"
      height="20"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="3"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <polyline points="20 6 9 17 4 12" />
    </svg>
  );
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
