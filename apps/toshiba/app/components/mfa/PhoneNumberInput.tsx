"use client";

import { useState } from "react";

interface PhoneNumberInputProps {
  value: string;
  onChange: (value: string) => void;
  error?: string;
  disabled?: boolean;
  placeholder?: string;
}

export function PhoneNumberInput({
  value,
  onChange,
  error,
  disabled = false,
  placeholder = "Enter phone number",
}: PhoneNumberInputProps): JSX.Element {
  const [focused, setFocused] = useState(false);

  const formatPhoneNumber = (input: string): string => {
    // Remove all non-digit characters
    const digits = input.replace(/\D/g, "");

    // If it starts with 1 and has 11 digits, format as US number
    if (digits.length === 11 && digits.startsWith("1")) {
      return `+1 (${digits.slice(1, 4)}) ${digits.slice(4, 7)}-${digits.slice(7)}`;
    }

    // If it has 10 digits, assume US number and add +1
    if (digits.length === 10) {
      return `+1 (${digits.slice(0, 3)}) ${digits.slice(3, 6)}-${digits.slice(6)}`;
    }

    // For other lengths, just add + if not present
    if (digits.length > 0 && !input.startsWith("+")) {
      return `+${digits}`;
    }

    return input;
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (disabled) return;

    const input = e.target.value;

    // Allow + at the beginning and digits
    if (input === "" || /^(\+)?[\d\s\(\)\-]*$/.test(input)) {
      onChange(input);
    }
  };

  const handleBlur = () => {
    setFocused(false);
    if (value) {
      const formatted = formatPhoneNumber(value);
      onChange(formatted);
    }
  };

  const validatePhoneNumber = (phone: string): string | null => {
    const digits = phone.replace(/\D/g, "");

    if (digits.length < 10) {
      return "Phone number must be at least 10 digits";
    }

    if (digits.length > 15) {
      return "Phone number must be at most 15 digits";
    }

    return null;
  };

  const validationError = value ? validatePhoneNumber(value) : null;
  const displayError = error || validationError;

  return (
    <div className="ui-flex ui-flex-col ui-gap-2">
      <div style={{ position: "relative" }}>
        <input
          type="tel"
          value={value}
          onChange={handleChange}
          onFocus={() => setFocused(true)}
          onBlur={handleBlur}
          disabled={disabled}
          placeholder={placeholder}
          className={`
            ui-w-full ui-py-3 ui-rounded-lg ui-bg-[#161616] ui-text-white
            ui-border focus:ui-outline-none focus:ui-ring-2 focus:ui-ring-[#E75F33]
            ${displayError ? "ui-border-red-500" : "ui-border-gray-600"}
            ${disabled ? "ui-opacity-50 ui-cursor-not-allowed" : ""}
            ${focused ? "ui-ring-2 ui-ring-[#E75F33]" : ""}
          `}
          style={{
            borderColor: "var(--ev-colors-highlight)",
            paddingLeft: "48px",
            paddingRight: "16px",
          }}
        />
        <div
          style={{
            position: "absolute",
            left: "12px",
            top: "50%",
            transform: "translateY(-50%)",
            pointerEvents: "none",
            color: "var(--ev-colors-secondaryText)",
          }}
        >
          <PhoneIcon />
        </div>
      </div>
      {displayError && (
        <p className="ui-text-sm ui-text-red-500">{displayError}</p>
      )}
      <p className="ui-text-xs ui-text-gray-400" style={{ marginTop: "8px" }}>
        Enter your phone number with country code (e.g., +1 for US)
      </p>
    </div>
  );
}

function PhoneIcon(): JSX.Element {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width={18}
      height={18}
      fill="none"
      viewBox="0 0 24 24"
    >
      <path
        fill="#898989"
        d="M6.62 10.79c1.44 2.83 3.76 5.14 6.59 6.59l2.2-2.2c.27-.27.67-.36 1.02-.24 1.12.37 2.33.57 3.57.57.55 0 1 .45 1 1V20c0 .55-.45 1-1 1-9.39 0-17-7.61-17-17 0-.55.45-1 1-1h3.5c.55 0 1 .45 1 1 0 1.25.2 2.45.57 3.57.11.35.03.74-.25 1.02l-2.2 2.2z"
      />
    </svg>
  );
}
