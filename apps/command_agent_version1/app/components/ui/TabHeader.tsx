"use client";

import React from "react";

interface Tab {
	id: string;
	label: string;
	disabled?: boolean;
}

interface TabHeaderProps {
	tabs: Tab[];
	activeTab: string;
	onTabChange: (tabId: string) => void;
	showToggleButton?: boolean;
	toggleButtonState?: boolean;
	onToggle?: () => void;
	ToggleIcon?: React.ComponentType;
	ToggleIconActive?: React.ComponentType;
	className?: string;
	tabClassName?: string;
	activeTabClassName?: string;
	inactiveTabClassName?: string;
}

function TabHeader({
	tabs,
	activeTab,
	onTabChange,
	showToggleButton = false,
	toggleButtonState = false,
	onToggle,
	ToggleIcon,
	ToggleIconActive,
	className = "",
	tabClassName = "flex-1 text-center py-1 px-4 rounded-4 text-xs cursor-pointer",
	activeTabClassName = "active font-medium bg-white text-orange-500",
	inactiveTabClassName = "text-gray-500 hover:text-orange-500"
}: TabHeaderProps): JSX.Element {
	return (
		<div className={`bg-white flex items-center justify-between ${className}`}>
			<div className="p-1 rounded-lg flex items-center w-full">
				{tabs.map((tab) => (
					<button
						key={tab.id}
						className={`${tabClassName} ${activeTab === tab.id ? activeTabClassName : inactiveTabClassName
							} ${tab.disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
						onClick={() => { !tab.disabled && onTabChange(tab.id) }}
						type="button"
						disabled={tab.disabled}
					>
						{tab.label}
					</button>
				))}
			</div>

			{showToggleButton && onToggle && (ToggleIcon ?? ToggleIconActive) ? <button type="button" onClick={onToggle}>
				{toggleButtonState && ToggleIconActive ? (
					<ToggleIconActive />
				) : ToggleIcon ? (
					<ToggleIcon />
				) : null}
			</button> : null}
		</div>
	);
}

export default TabHeader;
export type { Tab, TabHeaderProps };
