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
      </label>
      <div className="config-field-content">{children}</div>
    </div>
  );
}