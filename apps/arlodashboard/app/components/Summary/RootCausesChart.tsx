import React from 'react';
import {
    ResponsiveContainer,
    BarChart,
    Bar,
    XAxis,
    YAxis,
    Tooltip,
    Legend,
    TooltipProps
} from 'recharts';
import { RootCause } from './types';

// Custom tooltip component for bar chart
const CustomTooltip = ({ active, payload, label }: TooltipProps<number, string>) => {
    if (active && payload && payload.length) {
        const percentage = payload[0].payload?.percentage;
        const formattedPercentage = typeof percentage === 'number'
            ? percentage.toFixed(1)
            : '0';

        return (
            <div className="bg-white p-2 border border-gray-200 shadow-md rounded-md text-sm">
                <p className="font-medium">{label}</p>
                <p className="text-blue-600">{`Sessions: ${payload[0].value}`}</p>
                <p className="text-gray-600">{`Percentage: ${formattedPercentage}%`}</p>
            </div>
        );
    }
    return null;
};

interface RootCausesChartProps {
    rootCauses: RootCause[];
}

export const RootCausesChart: React.FC<RootCausesChartProps> = ({ rootCauses }) => {
    // Filter out the "Disconnected Phone" and "Offline" categories
    const filteredRootCauses = rootCauses.filter(
        cause => cause.name !== "Disconnected Phone" && cause.name !== "Offline"
    );

    return (
        <div className="bg-white rounded shadow border border-gray-200 h-full">
            <div className="bg-blue-700 text-white text-center py-2 font-semibold">
                Top Issues Distribution
            </div>
            <div className="p-4">
                <div className="h-64 w-full">
                    <ResponsiveContainer width="100%" height="100%">
                        <BarChart
                            data={filteredRootCauses}
                            margin={{ top: 5, right: 20, left: 20 }}
                        >
                            <XAxis
                                dataKey="name"
                                tick={{ fill: '#4a5568', fontSize: 12 }}
                                axisLine={{ stroke: '#cbd5e0' }}
                                tickLine={{ stroke: '#cbd5e0' }}
                                height={60}
                            />
                            <YAxis
                                tick={{ fill: '#4a5568', fontSize: 12 }}
                                axisLine={{ stroke: '#cbd5e0' }}
                                tickLine={{ stroke: '#cbd5e0' }}
                            />
                            <Tooltip content={<CustomTooltip />} />
                            <Legend
                                wrapperStyle={{
                                    bottom: 0,
                                    fontSize: '12px'
                                }}
                            />
                            <Bar
                                dataKey="sessions"
                                name="Number of Sessions"
                                fill="#2196F3"
                                barSize={30}
                            />
                        </BarChart>
                    </ResponsiveContainer>
                </div>
            </div>
        </div>
    );
};