"use client";

import React from "react";
import PromptDashboard from "../components/PromptDashboard";
//import "./page.scss";

export default function Prompt(): JSX.Element {
  return (
    <main className="flex" style={{
      height: '100vh',
      overflow: 'auto',
      position: 'relative',
      paddingTop: '52px'
    }}>
      <PromptDashboard />
    </main>
  );
}