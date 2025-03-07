import React from 'react';

interface CircularProgressProps {
    value: number | string;
    maxValue: number;
    size?: number;
    strokeWidth?: number;
    backgroundColor?: string;
    progressColor?: string;
    children?: React.ReactNode;
}

export const CircularProgress: React.FC<CircularProgressProps> = ({
    value,
    maxValue,
    size = 96,
    strokeWidth = 8,
    backgroundColor = '#e2e8f0',
    progressColor = '#4CAF50',
    children
}) => {
    // Determine the type of value
    const isTimeFormat = typeof value === 'string' && value.includes(':');
    const isPercentage = typeof value === 'string' && value.includes('%');

    // Calculate radius
    const radius = (size - strokeWidth) / 2;

    // Calculate circumference
    const circumference = 2 * Math.PI * radius;

    // Parse value to determine percentage of arc to show
    let progressPercentage: number;
    if (isTimeFormat) {
        // For time format (22:03), show 75% of the circle
        progressPercentage = 75;
    } else if (isPercentage) {
        // For percentage (8.7%), use actual percentage for the arc
        progressPercentage = parseFloat(value as string);
    } else if (typeof value === 'number') {
        // For numbers (total sessions), calculate percentage of max
        progressPercentage = Math.min(100, (value / maxValue) * 100);
    } else {
        // Fallback
        progressPercentage = 0;
    }

    // Calculate stroke dash offset
    const strokeDashoffset = circumference - (progressPercentage / 100) * circumference;

    return (
        <div className="relative inline-flex" style={{ width: size, height: size }}>
            <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className="rotate-[-90deg]">
                {/* Background circle */}
                <circle
                    cx={size / 2}
                    cy={size / 2}
                    r={radius}
                    strokeWidth={strokeWidth}
                    stroke={backgroundColor}
                    fill="none"
                />

                {/* Progress circle */}
                <circle
                    cx={size / 2}
                    cy={size / 2}
                    r={radius}
                    strokeWidth={strokeWidth}
                    stroke={progressColor}
                    fill="none"
                    strokeDasharray={circumference}
                    strokeDashoffset={strokeDashoffset}
                    strokeLinecap="round"
                />
            </svg>

            {/* Content in the center */}
            <div className="absolute inset-0 flex items-center justify-center">
                {children}
            </div>
        </div>
    );
};