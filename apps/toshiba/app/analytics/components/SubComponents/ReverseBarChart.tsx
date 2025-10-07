import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, ResponsiveContainer, Tooltip, Cell } from 'recharts';

interface ReverseBarChartProps {
    data: Array<{
        category: string;
        value: number;
    }>;
}

const ReverseBarChart: React.FC<ReverseBarChartProps> = ({ data }) => {
    const categoryColors = {
        "Touch Screen Failure": "#FF6B00",
        "Scanner Problems": "#FFB800",
        "Printer Issues": "#F8E897",
        "Power Problems": "#9F4B53",
        "Software Errors": "#D71313",
        "Network Connectivity": "#E16D40",
        "Hardware Damage": "#93000A",
        "RFID Reader Issues": "#8B0000",
        "Other": "#C2C2C2"
    };

    const defaultColor = "#8884d8";

    const getCategoryColor = (category: string) => {
        return categoryColors[category] || defaultColor;
    };

    const sortedData = [...data].sort((a, b) => a.value - b.value);

    return (
        <ResponsiveContainer width="100%" height={300}>
            <BarChart
                layout="vertical"
                data={sortedData}
                margin={{ top: 10, right: 20, left: 130, bottom: 10 }}
            >
                <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                <XAxis type="number" />
                <YAxis
                    type="category"
                    dataKey="category"
                    width={120}
                    tick={{ fontSize: 12 }}
                />
                <Tooltip
                    formatter={(value) => [`${value}`, 'Count']}
                    labelFormatter={(value) => `Category: ${value}`}
                />
                <Bar
                    dataKey="value"
                    radius={[0, 4, 4, 0]}
                    barSize={20}
                >
                    {sortedData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={getCategoryColor(entry.category)} />
                    ))}
                </Bar>
            </BarChart>
        </ResponsiveContainer>
    );
};

export default ReverseBarChart;