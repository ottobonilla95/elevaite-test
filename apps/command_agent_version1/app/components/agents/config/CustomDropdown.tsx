"use client";
import React, { useState, useEffect, useRef } from "react";
import "./CustomDropdown.scss";

export interface DropdownOption {
  value: string;
  label: string;
  disabled?: boolean;
}

interface CustomDropdownProps {
  options: DropdownOption[];
  defaultValue?: string;
  placeholder?: string;
  onChange?: (value: string) => void;
  textColor?: string;
  value?: string;
}

export function CustomDropdown({
  options,
  defaultValue,
  placeholder = "Select an option",
  onChange,
  textColor = "#374151",
  value,
}: CustomDropdownProps): JSX.Element {
  const [isOpen, setIsOpen] = useState(false);
  const [selectedValue, setSelectedValue] = useState(
    value ??
      defaultValue ??
      (options.length > 0 && !options[0].disabled ? options[0].value : "")
  );
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Update selected value when value prop changes
  useEffect(() => {
    if (value !== undefined) {
      setSelectedValue(value);
    }
  }, [value]);

  // Find the label for the selected value
  const selectedLabel =
    options.find((option) => option.value === selectedValue)?.label ??
    placeholder;

  // Handle click outside to close dropdown
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent): void => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false);
      }
    };

    const handleScroll = (): void => {
      if (isOpen) {
        setIsOpen(false);
      }
    };

    const handleResize = (): void => {
      if (isOpen) {
        setIsOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    window.addEventListener("scroll", handleScroll, true);
    window.addEventListener("resize", handleResize);

    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
      window.removeEventListener("scroll", handleScroll, true);
      window.removeEventListener("resize", handleResize);
    };
  }, [isOpen]);

  const handleOptionClick = (optionValue: string, disabled?: boolean): void => {
    if (disabled) return;

    setSelectedValue(optionValue);
    setIsOpen(false);
    if (onChange) {
      onChange(optionValue);
    }
  };

  const handleKeyDown = (event: React.KeyboardEvent): void => {
    switch (event.key) {
      case "Enter":
      case " ":
        event.preventDefault();
        setIsOpen(!isOpen);
        break;
      case "Escape":
        setIsOpen(false);
        break;
      case "ArrowDown":
        event.preventDefault();
        if (!isOpen) {
          setIsOpen(true);
        }
        break;
      case "ArrowUp":
        event.preventDefault();
        if (!isOpen) {
          setIsOpen(true);
        }
        break;
    }
  };

  const handleOptionKeyDown = (
    event: React.KeyboardEvent,
    optionValue: string,
    disabled?: boolean
  ): void => {
    switch (event.key) {
      case "Enter":
      case " ":
        event.preventDefault();
        handleOptionClick(optionValue, disabled);
        break;
      case "Escape":
        setIsOpen(false);
        break;
    }
  };

  return (
    <div ref={dropdownRef} className="custom-dropdown">
      {/* Dropdown Button */}
      <div
        className="dropdown-button"
        role="button"
        tabIndex={0}
        aria-expanded={isOpen}
        aria-haspopup="listbox"
        onClick={() => {
          setIsOpen(!isOpen);
        }}
        onKeyDown={handleKeyDown}
      >
        <span style={{ color: textColor }}>{selectedLabel}</span>
        <svg
          className={`dropdown-arrow ${isOpen ? "open" : ""}`}
          fill="none"
          viewBox="0 0 16 16"
          width={16}
          height={16}
          xmlns="http://www.w3.org/2000/svg"
        >
          <path
            d="m4 6.5 4 4 4-4"
            stroke={textColor}
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1.5}
          />
        </svg>
      </div>

      {/* Dropdown Options */}
      {isOpen ? (
        <div className="dropdown-menu" role="listbox">
          {options.map((option) => (
            <div
              key={option.value}
              className={`dropdown-option ${selectedValue === option.value ? "selected" : ""} ${option.disabled ? "disabled" : ""}`}
              role="option"
              tabIndex={option.disabled ? -1 : 0}
              aria-selected={selectedValue === option.value}
              aria-disabled={option.disabled}
              onClick={() => {
                handleOptionClick(option.value, option.disabled);
              }}
              onKeyDown={(event) => {
                handleOptionKeyDown(event, option.value, option.disabled);
              }}
            >
              {option.label}
            </div>
          ))}
        </div>
      ) : null}
    </div>
  );
}
