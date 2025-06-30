"use client";

import React from "react";

interface PillProps {
	text: string;
	textColor?: string;
	backgroundColor?: string;
	className?: string;
}

function Pill({
	text,
	textColor = "#374151", // gray-700 default
	backgroundColor = "#f3f4f6", // gray-100 default
	className = ""
}: PillProps): JSX.Element {
	const pillStyle = {
		color: textColor,
		backgroundColor,
		borderRadius: "6px",
		padding: "4px 10px",
		display: "inline-block",
		fontSize: "12px",
		fontWeight: "500",
		lineHeight: "1.6",
		whiteSpace: "nowrap" as const
	};

	return (
		<span
			className={`pill ${className}`}
			style={pillStyle}
		>
			{text}
		</span>
	);
}

export default Pill;
export type { PillProps };
