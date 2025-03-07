import React from 'react';
import { CircularProgress } from './CircularProgress';

interface MetricCardProps {
    title: string;
    value: number | string;
    maxValue: number;
    subtitle: string;
    progressColor?: string;
}

export const MetricCard: React.FC<MetricCardProps> = ({
    title,
    value,
    maxValue,
    subtitle,
    progressColor = '#4CAF50'
}) => {
    // Format values for display if needed
    let displayValue = value;

    // For large numbers, use thousand separators
    if (typeof value === 'number' && value >= 1000) {
        displayValue = value.toLocaleString();
    }

    return (
        <div className="bg-white rounded shadow-md h-full">
            <div className="bg-blue-700 text-white text-center py-2 font-semibold">
                {title}
            </div>
            <div className="flex flex-col items-center justify-center py-4 px-4">
                <CircularProgress
                    value={value}
                    maxValue={maxValue}
                    progressColor={progressColor}
                    size={90}
                    strokeWidth={8}
                >
                    <span className="text-lg font-bold">{displayValue}</span>
                </CircularProgress>
                <p className="text-xs text-gray-500 mt-2 text-center">
                    {subtitle}
                </p>
            </div>
        </div>
    );
};