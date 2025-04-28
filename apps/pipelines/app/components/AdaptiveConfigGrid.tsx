"use client";
import React, { ReactNode, useRef } from "react";
import "./AdaptiveConfigGrid.scss";

export interface ConfigOption {
  id: string;
  children: ReactNode;
}

interface AdaptiveConfigGridProps {
  options: ConfigOption[];
}

export function AdaptiveConfigGrid({
  options,
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

  return (
    <div className="adaptive-config-container" ref={containerRef}>
      <div
        className="adaptive-config-grid"
        style={{
          gridTemplateColumns: columns > 1 ? `repeat(${columns}, 1fr)` : "1fr",
          overflow: columns === 1 ? "auto" : "visible",
          transition: "none", // Disable transitions to prevent visual glitches
        }}
      >
        {options.map((option) => (
          <div key={option.id} className="config-option">
            {option.children}
          </div>
        ))}
      </div>
    </div>
  );
}
