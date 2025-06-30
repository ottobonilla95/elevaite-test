"use client";
import React from "react";

interface CustomInputProps {
  type?: "text" | "password" | "number";
  placeholder?: string;
  defaultValue?: string;
  onChange?: (value: string) => void;
}

export function CustomInput({
  type = "text",
  placeholder = "",
  defaultValue = "",
  onChange,
}: CustomInputProps): JSX.Element {
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (onChange) {
      onChange(e.target.value);
    }
  };

  return (
    <input
      type={type}
      placeholder={placeholder}
      defaultValue={defaultValue}
      onChange={handleChange}
      style={{
        backgroundColor: "#212124",
        color: "white",
        border: "2px solid #3f3f41",
        padding: "10px",
        borderRadius: "8px",
        fontSize: "14px",
        width: "100%",
        height: "40px",
        boxSizing: "border-box",
      }}
    />
  );
}
