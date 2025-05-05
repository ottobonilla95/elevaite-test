"use client";
import React, { ReactNode, useRef } from "react";
import "./AdaptiveConfigGrid.scss";

export interface ConfigOption {
  id: string;
  children: ReactNode;
}

interface AdaptiveConfigGridProps {
  options: ConfigOption[];
  containerClassName?: string;
}

export function AdaptiveConfigGrid({
  options,
  containerClassName = "",
}: AdaptiveConfigGridProps): JSX.Element {
  // Always use 2 columns, with 4 options per column (or 3 if needed)
  const columns = 2;
  const containerRef = useRef<HTMLDivElement>(null);

  const groupOptionsIntoColumns = () => {
    const result: ConfigOption[][] = [];

    // Always limit to 3 options per column
    const optionsPerColumn = 3;

    // Special cases for even distribution
    if (options.length === 1) {
      // For 1 option, put it in first column and add empty second column
      result.push(options);
      result.push([]);
      return result;
    } else if (options.length === 2) {
      // For 2 options, put 1 in each column
      result.push(options.slice(0, 1));
      result.push(options.slice(1));
      return result;
    } else if (options.length === 3) {
      // For 3 options, put 2 in first column, 1 in second
      result.push(options.slice(0, 2));
      result.push(options.slice(2));
      return result;
    } else if (options.length <= 4) {
      // For 4 options, put 2 in each column
      result.push(options.slice(0, 2));
      result.push(options.slice(2));
      return result;
    } else if (options.length === 5) {
      // For 5 options, put 3 in first column, 2 in second
      result.push(options.slice(0, 3));
      result.push(options.slice(3));
      return result;
    } else if (options.length === 6) {
      // For 6 options, put 3 in each column
      result.push(options.slice(0, 3));
      result.push(options.slice(3));
      return result;
    }

    // Distribute according to optionsPerColumn
    for (let i = 0; i < columns; i++) {
      const startIndex = i * optionsPerColumn;
      const endIndex = Math.min(startIndex + optionsPerColumn, options.length);
      const columnOptions = options.slice(startIndex, endIndex);

      if (columnOptions.length > 0) {
        result.push(columnOptions);
      }
    }

    return result;
  };

  const columnGroups = groupOptionsIntoColumns();

  return (
    <div
      className={`adaptive-config-container ${containerClassName}`}
      ref={containerRef}
    >
      <div
        className="adaptive-config-grid"
        style={{
          gridTemplateColumns: `repeat(${columns}, 1fr)`, // Always use 2 columns
          transition: "none", // Disable transitions to prevent visual glitches
        }}
      >
        {columnGroups.map((columnOptions, columnIndex) => (
          <div key={`column-${columnIndex}`} className="config-column">
            {columnOptions.map((option) => (
              <div key={option.id} className="config-option">
                {option.children}
              </div>
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}
