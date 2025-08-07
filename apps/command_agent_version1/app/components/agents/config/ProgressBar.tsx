"use client";

import React from "react";
import "./ProgressBar.scss";

interface ProgressBarProps {
  progress: number;
  isRunning: boolean;
  label?: string;
  icon?: string;
}

export function ProgressBar({ progress, isRunning, label, icon }: ProgressBarProps): JSX.Element {
  return (
    <div className="progress-bar-container">
      <div className="progress-info">
        {icon && <span className="progress-icon">{icon}</span>}
        <span className="progress-label">{label || "Processing..."}</span>
        <span className="progress-percentage">{Math.round(progress)}%</span>
      </div>
      <div className="progress-bar">
        <div 
          className={`progress-fill ${isRunning ? "animated" : ""}`}
          style={{ width: `${progress}%` }}
        />
      </div>
    </div>
  );
}