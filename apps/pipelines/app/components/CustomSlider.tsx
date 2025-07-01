"use client";
import React from "react";
import "./CustomSlider.scss";

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
    <div className="custom-slider-container">
      <div className="slider-value-display">
        <span className="current-value">Current: {currentValue}</span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={currentValue}
        onChange={handleChange}
        className="custom-slider"
      />
      <div className="slider-range-labels">
        <span className="min-value">{min}</span>
        <span className="max-value">{max}</span>
      </div>
    </div>
  );
}
