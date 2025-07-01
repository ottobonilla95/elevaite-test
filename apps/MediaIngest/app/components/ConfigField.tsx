"use client";
import React, { ReactNode, useRef, useState } from "react";
import "./ConfigField.scss";

interface ConfigFieldProps {
  label: string;
  children: ReactNode;
  tooltip?: string;
}

export function ConfigField({
  label,
  children,
  tooltip,
}: ConfigFieldProps): JSX.Element {
  const tooltipRef = useRef<HTMLDivElement>(null);
  const iconRef = useRef<HTMLSpanElement>(null);
  const [tooltipStyle, setTooltipStyle] = useState<React.CSSProperties>({});

  const handleMouseEnter = () => {
    if (iconRef.current && tooltipRef.current) {
      const iconRect = iconRef.current.getBoundingClientRect();
      const tooltipWidth = 220;

      setTooltipStyle({
        top: iconRect.top - 60,
        left: iconRect.left + iconRect.width / 2 - tooltipWidth / 2,
      });
    }
  };

  return (
    <div className="config-field">
      <div className="config-field-label-container">
        <label className="config-field-label">{label}</label>
        {tooltip && (
          <div className="tooltip-container" onMouseEnter={handleMouseEnter}>
            <span ref={iconRef} className="tooltip-icon">
              ?
            </span>
            <div ref={tooltipRef} className="tooltip-text" style={tooltipStyle}>
              {tooltip}
            </div>
          </div>
        )}
      </div>
      <div className="config-field-content">{children}</div>
    </div>
  );
}
