import React from 'react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid, Cell, LabelList } from 'recharts';

interface CustomBarChartProps {
    data: Array<{
        label: string;
        count: number;
        color: string;
    }>;
}

const CustomTooltip = ({ active, payload, label }: {
    active?: boolean;
    payload?: Array<{ value: number; color: string }>;
    label?: string;
}) => {
    if (active && payload && payload.length) {
        return (
            <div style={{
                backgroundColor: 'rgba(255, 255, 255, 0.98)',
                border: '1px solid #e5e7eb',
                borderRadius: '8px',
                padding: '12px',
                boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
                fontSize: '13px',
                minWidth: '180px'
            }}>
                <p style={{
                    margin: '0 0 6px 0',
                    fontWeight: '600',
                    color: '#111927',
                    fontSize: '14px'
                }}>
                    Machine Type: {label}
                </p>
                <p style={{
                    margin: 0,
                    color: payload[0].color,
                    fontWeight: '500',
                    fontSize: '13px'
                }}>
                    Service Requests: {payload[0].value.toLocaleString()}
                </p>
            </div>
        );
    }
    return null;
};

const CustomBarChart: React.FC<CustomBarChartProps> = ({ data }) => {
    return (
        <div style={{ width: '100%', height: '320px', padding: '0', margin: '0' }}>
            <ResponsiveContainer width="100%" height="100%">
                <BarChart
                    data={data}
                    margin={{
                        top: 25,
                        right: 30,
                        left: 20,
                        bottom: 40
                    }}
                    barCategoryGap="20%"
                >
                    <CartesianGrid strokeDasharray="0" vertical={false} stroke="#f0f0f0" />
                    <XAxis
                        dataKey="label"
                        tick={{ fontSize: 12, fill: '#64748b' }}
                        axisLine={{ stroke: '#e5e7eb' }}
                        tickLine={{ stroke: '#e5e7eb' }}
                        angle={-35}
                        textAnchor="end"
                        height={50}
                        interval={0}
                    />
                    <YAxis
                        tick={{ fontSize: 11, fill: '#64748b' }}
                        axisLine={{ stroke: '#e5e7eb' }}
                        tickLine={{ stroke: '#e5e7eb' }}
                        width={60}
                    />
                    <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255, 104, 31, 0.1)' }} />
                    <Bar
                        dataKey="count"
                        radius={[6, 6, 0, 0]}
                        maxBarSize={80}
                        stroke="rgba(255, 255, 255, 0.8)"
                        strokeWidth={1}
                    >
                        {data.map((entry, index) => (
                            <Cell
                                key={`cell-${index}`}
                                fill={entry.color || '#FF681F'}
                            />
                        ))}
                        <LabelList
                            dataKey="count"
                            position="top"
                            style={{
                                fontSize: '11px',
                                fill: '#64748b',
                                fontWeight: '500'
                            }}
                            offset={8}
                        />
                    </Bar>
                </BarChart>
            </ResponsiveContainer>
        </div>
    );
};

export default CustomBarChart;

