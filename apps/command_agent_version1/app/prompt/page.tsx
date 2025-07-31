"use client";

import React from "react";
import { X } from "lucide-react";
import { ToastContainer } from 'react-toastify';
import PromptDashboard from "../components/PromptDashboard";
import "./page.scss";

function CloseButton({ closeToast }: { closeToast: () => void }): React.ReactElement {
  return <button type="button" onClick={closeToast}>
		<X size={12} color="white" />
	</button>
}

export default function Prompt(): JSX.Element {
	return (
		<main className="main-prompts-container">
			<PromptDashboard />
			<ToastContainer closeButton={CloseButton} />
		</main>
	);
}