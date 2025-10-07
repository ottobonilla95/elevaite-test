import React from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer } from 'recharts';
import './DonutChart.scss';

interface DonutChartProps {
    data: Array<{
        name: string;
        value: number;
        color: string;
    }>;
    totalTickets: number;
}

const DonutChart: React.FC<DonutChartProps> = ({ data, totalTickets }) => {
    return (
        <div className="donut-chart-wrapper">
            <div className="chart-container">
                <ResponsiveContainer width={240} height={240}>
                    <PieChart>
                        <Pie
                            data={data}
                            cx="50%"
                            cy="50%"
                            innerRadius={70}
                            outerRadius={100}
                            dataKey="value"
                            nameKey="name"
                        >
                            {data.map((entry, index) => (
                                <Cell key={`cell-${index}`} fill={entry.color} />
                            ))}
                        </Pie>
                        <text x="50%" y="50%" textAnchor="middle" dominantBaseline="middle">
                            <tspan x="50%" dy="-10" fontSize="14" fill="#999">Tickets</tspan>
                            <tspan x="50%" dy="30" fontSize="28" fontWeight="600" fill="#333">{totalTickets}</tspan>
                        </text>
                    </PieChart>
                </ResponsiveContainer>
            </div>

            <div className="legend-container">
                {data.map((item, index) => (
                    <div key={index} className="legend-item">
                        <span
                            className="legend-dot"
                            style={{ backgroundColor: item.color }}
                        />
                        <span className="legend-text">
                            {item.name} {item.value}%
                        </span>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default DonutChart;