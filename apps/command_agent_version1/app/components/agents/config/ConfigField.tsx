"use client";
import React, { type ReactNode } from "react";
import "./ConfigField.scss";

interface ConfigFieldProps {
  label: string;
  children: ReactNode;
  description?: string;
}

export function ConfigField({
  label,
  children,
  description,
}: ConfigFieldProps): JSX.Element {
  return (
    <div className="config-field">
      <label className="config-field-label">
        {label}
        {description ? (
          <span className="config-field-description" title={description}>
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="14"
              height="14"
              viewBox="0 0 24 24"
              fill="currentColor"
            >
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z" />
            </svg>
          </span>
        ) : null}
      </label>
      <div className="config-field-content">{children}</div>
    </div>
  );
}
