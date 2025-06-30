"use client";
import React, { ReactNode } from "react";
import "./ConfigField.scss";

interface ConfigFieldProps {
  label: string;
  children: ReactNode;
}

export function ConfigField({ label, children }: ConfigFieldProps): JSX.Element {
  return (
    <div className="config-field">
      <label className="config-field-label">{label}</label>
      <div className="config-field-content">{children}</div>
    </div>
  );
}
