"use client";

import React from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, TooltipProps } from 'recharts';
import './MachineTypesPieChart.scss';

interface MachineTypesChartProps {
    data: Array<{
        name: string;
        value: number;
        count: number;
        color: string;
    }>;
}

const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
        const data = payload[0].payload;
        return (
            <div className="machine-types-tooltip">
                <p className="tooltip-name">{data.name}</p>
                <p className="tooltip-value">{data.count} machines</p>
            </div>
        );
    }
    return null;
};

const MachineTypesPieChart: React.FC<MachineTypesChartProps> = ({ data }) => {
    if (!data || data.length === 0) {
        return <div>No data available</div>;
    }

    const validData = data.filter(item => !isNaN(item.value) && item.value > 0);

    return (
        <div className="machine-types-pie-container">
            <div className="chart-area">
                <ResponsiveContainer width="100%" height={350}>
                    <PieChart>
                        <Pie
                            data={validData}
                            cx="50%"
                            cy="50%"
                            labelLine={false}
                            outerRadius={120}
                            fill="#8884d8"
                            dataKey="value"
                        >
                            {validData.map((entry, index) => (
                                <Cell key={`cell-${index}`} fill={entry.color} />
                            ))}
                        </Pie>
                        <Tooltip content={<CustomTooltip />} />
                    </PieChart>
                </ResponsiveContainer>
            </div>

            {/* Custom legend that exactly matches the Figma design */}
            <div className="machine-types-legend">
                {data.map((item, index) => (
                    <div key={index} className="legend-item">
                        <div className="legend-bullet" style={{ backgroundColor: item.color }}></div>
                        <div className="legend-content">
                            <div className="legend-main-info">
                                <span className="legend-name">{item.name}</span>
                                <span className="legend-percentage">{item.value}%</span>
                            </div>
                            <div className="legend-count">Machine Count: {item.count}</div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default MachineTypesPieChart;

