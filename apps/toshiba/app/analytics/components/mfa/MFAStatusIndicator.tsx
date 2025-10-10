"use client";

interface MFAStatusIndicatorProps {
  mfaEnabled: boolean;
  smsMfaEnabled?: boolean;
  phoneVerified?: boolean;
  className?: string;
}

export function MFAStatusIndicator({
  mfaEnabled,
  smsMfaEnabled = false,
  phoneVerified = false,
  className = "",
}: MFAStatusIndicatorProps): JSX.Element {
  const getMFAStatus = () => {
    if (mfaEnabled && smsMfaEnabled && phoneVerified) {
      return {
        status: "Both TOTP and SMS MFA enabled",
        color: "ui-text-green-500",
        icon: <CheckCircleIcon />,
        bgColor: "ui-bg-green-100",
      };
    } else if (mfaEnabled) {
      return {
        status: "TOTP MFA enabled",
        color: "ui-text-green-500",
        icon: <CheckCircleIcon />,
        bgColor: "ui-bg-green-100",
      };
    } else if (smsMfaEnabled && phoneVerified) {
      return {
        status: "SMS MFA enabled",
        color: "ui-text-green-500",
        icon: <CheckCircleIcon />,
        bgColor: "ui-bg-green-100",
      };
    } else if (smsMfaEnabled && !phoneVerified) {
      return {
        status: "SMS MFA setup (phone not verified)",
        color: "ui-text-yellow-500",
        icon: <WarningIcon />,
        bgColor: "ui-bg-yellow-100",
      };
    } else {
      return {
        status: "MFA not enabled",
        color: "ui-text-red-500",
        icon: <XCircleIcon />,
        bgColor: "ui-bg-red-100",
      };
    }
  };

  const { status, color, icon, bgColor } = getMFAStatus();

  return (
    <div
      className={`ui-flex ui-items-center ui-gap-2 ui-p-3 ui-rounded-lg ${bgColor} ${className}`}
    >
      <div className={color}>{icon}</div>
      <span className={`ui-text-sm ui-font-medium ${color}`}>{status}</span>
    </div>
  );
}

function CheckCircleIcon(): JSX.Element {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width={20}
      height={20}
      fill="currentColor"
      viewBox="0 0 24 24"
    >
      <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z" />
    </svg>
  );
}

function WarningIcon(): JSX.Element {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width={20}
      height={20}
      fill="currentColor"
      viewBox="0 0 24 24"
    >
      <path d="M1 21h22L12 2 1 21zm12-3h-2v-2h2v2zm0-4h-2v-4h2v4z" />
    </svg>
  );
}

function XCircleIcon(): JSX.Element {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width={20}
      height={20}
      fill="currentColor"
      viewBox="0 0 24 24"
    >
      <path d="M12 2C6.47 2 2 6.47 2 12s4.47 10 10 10 10-4.47 10-10S17.53 2 12 2zm5 13.59L15.59 17 12 13.41 8.41 17 7 15.59 10.59 12 7 8.41 8.41 7 12 10.59 15.59 7 17 8.41 13.41 12 17 15.59z" />
    </svg>
  );
}
