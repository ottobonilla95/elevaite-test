"use client";
import React, { ReactNode, useEffect, useState, useRef } from "react";
import "./AdaptiveConfigGrid.scss";

export interface ConfigOption {
  id: string;
  children: ReactNode;
}

interface AdaptiveConfigGridProps {
  options: ConfigOption[];
}

export function AdaptiveConfigGrid({ options }: AdaptiveConfigGridProps): JSX.Element {
  const [columns, setColumns] = useState(1);
  const containerRef = useRef<HTMLDivElement>(null);
  
  // Function to calculate optimal column count
  const calculateOptimalColumns = () => {
    if (!containerRef.current) return 1;
    
    const containerHeight = containerRef.current.clientHeight;
    const optionCount = options.length;
    
    // Simple heuristic: if we have more than 3 options and enough height,
    // switch to multi-column layout
    if (optionCount <= 3) {
      return 1; // Keep single column for 3 or fewer options
    } else if (optionCount <= 6) {
      return 2; // Use 2 columns for 4-6 options
    } else {
      return 3; // Use 3 columns for 7+ options
    }
  };

  // Recalculate columns on resize or when options change
  useEffect(() => {
    const handleResize = () => {
      setColumns(calculateOptimalColumns());
    };
    
    handleResize(); // Initial calculation
    window.addEventListener('resize', handleResize);
    
    return () => {
      window.removeEventListener('resize', handleResize);
    };
  }, [options.length]);

  return (
    <div className="adaptive-config-container" ref={containerRef}>
      <div 
        className="adaptive-config-grid" 
        style={{ 
          gridTemplateColumns: columns > 1 
            ? `repeat(${columns}, 1fr)` 
            : '1fr',
          overflow: columns === 1 ? 'auto' : 'visible'
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
