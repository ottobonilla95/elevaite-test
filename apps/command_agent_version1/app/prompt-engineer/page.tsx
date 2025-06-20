"use client";

import React from "react";
import PromptDashboard from "../components/PromptDashboard";
import "./page.scss";
import { ToastContainer } from 'react-toastify';

const CloseButton = ({ closeToast }) => (
	<button onClick={closeToast	}>
		<svg width="12" height="13" viewBox="0 0 12 13" fill="none" xmlns="http://www.w3.org/2000/svg">
			<path d="M11 1.5L1 11.5M1 1.5L11 11.5" stroke="white" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
		</svg>
	</button>
);

export default function Prompt(): JSX.Element {
  return (
    <main className="main-prompts-container">
      <PromptDashboard />
	  <ToastContainer closeButton={CloseButton}/>
    </main>
  );
}