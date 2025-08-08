"use client";

import React from "react";
import "./ProgressBar.scss";

interface ProgressBarProps {
  progress: number;
  isRunning: boolean;
  label?: string;
  icon?: React.ReactElement | string;
}

export function ProgressBar({ 
  progress, 
  isRunning, 
  label = "Processing...", 
  icon 
}: ProgressBarProps): JSX.Element {
  return (
    <div className="progress-bar-container">
      <div className="progress-info">
        <div className="progress-label">
          {icon && (
            <span className="progress-icon">
              {typeof icon === 'string' ? icon : icon}
            </span>
          )}
          <span className="progress-text">{label}</span>
        </div>
        <div className="progress-percentage">
          {Math.round(progress)}%
        </div>
      </div>
      
      <div className="progress-bar">
        <div 
          className={`progress-fill ${isRunning ? 'animated' : ''}`}
          style={{ width: `${progress}%` }}
        />
      </div>
      
      {isRunning && (
        <div className="progress-status">
          <span className="status-indicator">●</span>
          <span className="status-text">Running...</span>
        </div>
      )}
    </div>
  );
}