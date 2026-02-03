"use client";
import type { JSX, KeyboardEvent, ClipboardEvent, ChangeEvent } from "react";
import { useRef, useEffect } from "react";

interface MfaCodeInputProps {
  value: string;
  onChange: (value: string) => void;
  error?: string;
  disabled?: boolean;
  autoFocus?: boolean;
}

export function MfaCodeInput({
  value,
  onChange,
  error,
  disabled = false,
  autoFocus = true,
}: MfaCodeInputProps): JSX.Element {
  const inputRefs = useRef<(HTMLInputElement | null)[]>([]);
  const digits = value.padEnd(6, "").split("").slice(0, 6);

  useEffect(() => {
    if (autoFocus && inputRefs.current[0]) {
      inputRefs.current[0].focus();
    }
  }, [autoFocus]);

  const handleChange = (
    index: number,
    e: ChangeEvent<HTMLInputElement>,
  ): void => {
    const inputValue = e.target.value;

    // Only allow single digit
    if (inputValue.length > 1) {
      return;
    }

    // Only allow numbers
    if (inputValue && !/^\d$/.test(inputValue)) {
      return;
    }

    const newDigits = [...digits];
    newDigits[index] = inputValue;
    const newValue = newDigits.join("").replace(/\s/g, "");
    onChange(newValue);

    // Move to next input if digit entered
    if (inputValue && index < 5) {
      inputRefs.current[index + 1]?.focus();
    }
  };

  const handleKeyDown = (
    index: number,
    e: KeyboardEvent<HTMLInputElement>,
  ): void => {
    // Handle backspace
    if (e.key === "Backspace") {
      if (!digits[index] && index > 0) {
        // If current input is empty, move to previous and clear it
        inputRefs.current[index - 1]?.focus();
        const newDigits = [...digits];
        newDigits[index - 1] = "";
        onChange(newDigits.join("").replace(/\s/g, ""));
      }
    }

    // Handle arrow keys
    if (e.key === "ArrowLeft" && index > 0) {
      inputRefs.current[index - 1]?.focus();
    }
    if (e.key === "ArrowRight" && index < 5) {
      inputRefs.current[index + 1]?.focus();
    }
  };

  const handlePaste = (e: ClipboardEvent<HTMLInputElement>): void => {
    e.preventDefault();
    const pastedData = e.clipboardData.getData("text");
    const pastedDigits = pastedData.replace(/\D/g, "").slice(0, 6);

    if (pastedDigits) {
      onChange(pastedDigits);
      // Focus the input after the last pasted digit
      const focusIndex = Math.min(pastedDigits.length, 5);
      inputRefs.current[focusIndex]?.focus();
    }
  };

  const handleFocus = (e: React.FocusEvent<HTMLInputElement>): void => {
    e.target.select();
  };

  return (
    <div className="ui-flex ui-flex-col ui-gap-2 ui-w-full">
      <div className="ui-flex ui-gap-6 ui-justify-center">
        {[0, 1, 2, 3, 4, 5].map((index) => (
          <input
            key={index}
            ref={(el) => {
              inputRefs.current[index] = el;
            }}
            type="text"
            inputMode="numeric"
            maxLength={1}
            value={digits[index] ?? ""}
            onChange={(e) => {
              handleChange(index, e);
            }}
            onKeyDown={(e) => {
              handleKeyDown(index, e);
            }}
            onPaste={handlePaste}
            onFocus={handleFocus}
            disabled={disabled}
            className={`
              ui-flex-1 ui-max-w-[72px] ui-min-w-[48px]
              ui-bg-white
              ui-border-2 ui-rounded-lg
              ui-px-6 ui-py-3
              ui-text-[40px] ui-font-medium ui-text-[#212124]
              ui-text-center
              ui-outline-none ui-transition-colors
              ${error ? "ui-border-red-500" : "ui-border-[#FF681F]"}
              focus:ui-ring-2 focus:ui-ring-[#FF681F]
              disabled:ui-opacity-50 disabled:ui-cursor-not-allowed
            `}
            aria-label={`Digit ${index + 1} of 6`}
          />
        ))}
      </div>
      {error ? (
        <p className="ui-text-sm ui-text-red-500 ui-text-center">{error}</p>
      ) : null}
    </div>
  );
}
