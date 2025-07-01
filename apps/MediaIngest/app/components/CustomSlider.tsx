"use client";
import React from "react";

interface CustomSliderProps {
  defaultValue?: number;
  min?: number;
  max?: number;
  step?: number;
  onChange?: (value: number) => void;
}

export function CustomSlider({
  defaultValue = 0,
  min = 0,
  max = 1,
  step = 0.1,
  onChange,
}: CustomSliderProps): JSX.Element {
  const [currentValue, setCurrentValue] = React.useState(defaultValue);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = parseFloat(e.target.value);
    setCurrentValue(value);
    if (onChange) {
      onChange(value);
    }
  };

  return (
    <div style={{ width: "100%" }}>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "8px",
        }}
      >
        <span style={{ fontSize: "12px", color: "#666" }}>
          Current: {currentValue}
        </span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={currentValue}
        onChange={handleChange}
        style={{
          width: "100%",
          height: "6px",
          borderRadius: "3px",
          background: "#333",
          outline: "none",
          appearance: "none",
          WebkitAppearance: "none",
        }}
        className="custom-slider"
      />
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          marginTop: "8px",
          fontSize: "12px",
          color: "#666",
        }}
      >
        <span>{min}</span>
        <span>{max}</span>
      </div>
    </div>
  );
}
