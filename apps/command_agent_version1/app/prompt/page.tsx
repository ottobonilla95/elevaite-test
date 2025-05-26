"use client";

import React from "react";
import PromptDashboard from "../components/PromptDashboard";
import "./page.scss";

export default function Prompt(): JSX.Element {
  return (
    <main className="main-prompts-container">
      <PromptDashboard />
    </main>
  );
}