"use client";

import { useState, useRef, useEffect } from "react";

interface MFACodeInputProps {
  length?: number;
  onComplete: (code: string) => void;
  onCodeChange?: (code: string) => void;
  error?: string;
  disabled?: boolean;
  autoFocus?: boolean;
}

export function MFACodeInput({
  length = 6,
  onComplete,
  onCodeChange,
  error,
  disabled = false,
  autoFocus = true,
}: MFACodeInputProps): JSX.Element {
  const [code, setCode] = useState<string[]>(new Array(length).fill(""));
  const inputRefs = useRef<(HTMLInputElement | null)[]>([]);

  useEffect(() => {
    if (autoFocus && inputRefs.current[0]) {
      inputRefs.current[0].focus();
    }
  }, [autoFocus]);

  const handleChange = (index: number, value: string) => {
    if (disabled) return;

    // Only allow digits
    if (value && !/^\d$/.test(value)) return;

    const newCode = [...code];
    newCode[index] = value;
    setCode(newCode);

    const codeString = newCode.join("");
    onCodeChange?.(codeString);

    // Auto-focus next input
    if (value && index < length - 1) {
      inputRefs.current[index + 1]?.focus();
    }

    // Call onComplete when all digits are entered
    if (codeString.length === length) {
      onComplete(codeString);
    }
  };

  const handleKeyDown = (index: number, e: React.KeyboardEvent) => {
    if (disabled) return;

    if (e.key === "Backspace" && !code[index] && index > 0) {
      // Move to previous input on backspace if current is empty
      inputRefs.current[index - 1]?.focus();
    } else if (e.key === "ArrowLeft" && index > 0) {
      inputRefs.current[index - 1]?.focus();
    } else if (e.key === "ArrowRight" && index < length - 1) {
      inputRefs.current[index + 1]?.focus();
    }
  };

  const handlePaste = (e: React.ClipboardEvent) => {
    if (disabled) return;

    e.preventDefault();
    const pastedData = e.clipboardData.getData("text");
    const digits = pastedData.replace(/\D/g, "").slice(0, length);

    if (digits.length > 0) {
      const newCode = new Array(length).fill("");
      for (let i = 0; i < digits.length; i++) {
        newCode[i] = digits[i];
      }
      setCode(newCode);

      const codeString = newCode.join("");
      onCodeChange?.(codeString);

      // Focus the next empty input or the last input
      const nextIndex = Math.min(digits.length, length - 1);
      inputRefs.current[nextIndex]?.focus();

      if (codeString.length === length) {
        onComplete(codeString);
      }
    }
  };

  return (
    <div className="ui-flex ui-flex-col ui-gap-4">
      <div className="ui-flex ui-gap-3 ui-justify-start">
        {code.map((digit, index) => (
          <input
            key={index}
            ref={(el) => {
              inputRefs.current[index] = el;
            }}
            type="text"
            inputMode="numeric"
            maxLength={1}
            value={digit}
            onChange={(e) => handleChange(index, e.target.value)}
            onKeyDown={(e) => handleKeyDown(index, e)}
            onPaste={handlePaste}
            disabled={disabled}
            style={{
              border: "2px solid var(--ev-colors-highlight)",
              width: "60px",
              height: "96px",
              textAlign: "center",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
            className={`
              ui-text-2xl ui-font-mono ui-font-semibold
              ui-rounded-lg ui-text-white
              focus:ui-outline-none focus:ui-ring-2
              ${error ? "ui-border-red-500" : ""}
              ${disabled ? "ui-opacity-50 ui-cursor-not-allowed" : ""}
            `}
            style={
              {
                backgroundColor: "var(--ev-colors-inputBackground, #161616)",
                "--tw-ring-color": "var(--ev-colors-highlight)",
              } as React.CSSProperties
            }
          />
        ))}
      </div>
      {error && (
        <p className="ui-text-sm ui-text-red-500 ui-text-left">{error}</p>
      )}
    </div>
  );
}
