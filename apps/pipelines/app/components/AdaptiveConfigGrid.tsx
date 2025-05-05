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
  const columns = React.useMemo(() => {
    const optionCount = options.length;

    if (optionCount <= 2) {
      return 1;
    } else if (optionCount <= 4) {
      return 2;
    } else if (optionCount <= 8) {
      return 3;
    } else {
      return 4;
    }
  }, [options.length]);

  const containerRef = useRef<HTMLDivElement>(null);

  const groupOptionsIntoColumns = () => {
    const result: ConfigOption[][] = [];
    const optionsPerColumn = Math.ceil(options.length / columns);

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
          gridTemplateColumns: columns > 1 ? `repeat(${columns}, 1fr)` : "1fr",
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
