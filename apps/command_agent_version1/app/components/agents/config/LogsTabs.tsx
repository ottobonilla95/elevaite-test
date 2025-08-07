"use client";

import React from "react";
import "./LogsTabs.scss";

interface LogsTabsProps {
  activeTab: "logs" | "output";
  onTabChange: (tab: "logs" | "output") => void;
}

export function LogsTabs({ activeTab, onTabChange }: LogsTabsProps): JSX.Element {
  return (
    <div className="logs-tabs">
      <button
        type="button"
        className={`tab ${activeTab === "logs" ? "active" : ""}`}
        onClick={() => onTabChange("logs")}
      >
        Pipeline Execution Logs
      </button>
      <button
        type="button"
        className={`tab ${activeTab === "output" ? "active" : ""}`}
        onClick={() => onTabChange("output")}
      >
        Output
      </button>
    </div>
  );
}