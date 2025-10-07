import React, { useEffect } from 'react';
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';

interface CustomLineChartProps {
    data: Array<{
        date: string;
        value: number;
    }>;
    YAxislabel?: string;
}

const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
        return (
            <div style={{
                backgroundColor: 'rgba(255, 255, 255, 0.95)',
                border: '1px solid #e5e5e5',
                borderRadius: '8px',
                padding: '8px 12px',
                boxShadow: '0 2px 8px rgba(0,0,0,0.08)'
            }}>
                <p style={{ margin: 0, fontSize: '12px', color: '#666' }}>{label}</p>
                <p style={{ margin: 0, fontSize: '14px', fontWeight: 600, color: '#FF6B35' }}>
                    {payload[0].value.toLocaleString()}
                </p>
            </div>
        );
    }
    return null;
};

const CustomLineChart: React.FC<CustomLineChartProps> = ({ data, YAxislabel }) => {
    useEffect(() => {
        console.log("LineChart data:", data);
    }, [data]);

    if (!data || data.length === 0) {
        return (
            <div style={{ height: '280px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                No data available
            </div>
        );
    }

    const values = data.map(item => item.value);
    const maxValue = Math.max(...values);
    const tickCount = 5;
    const tickInterval = Math.ceil(maxValue / (tickCount - 1));
    const ticks = Array.from({ length: tickCount }, (_, i) => i * tickInterval);

    const labelInterval = Math.max(Math.floor(data.length / 6), 0);

    return (
        <ResponsiveContainer width="100%" height={280}>
            <AreaChart
                data={data}
                margin={{ top: 10, right: 10, left: 0, bottom: 30 }}
            >
                <defs>
                    <linearGradient id="colorGradient" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#FF6B35" stopOpacity={0.1} />
                        <stop offset="95%" stopColor="#FF6B35" stopOpacity={0} />
                    </linearGradient>
                </defs>
                <CartesianGrid
                    strokeDasharray="0"
                    stroke="#F3F4F6"
                />
                <XAxis
                    dataKey="date"
                    axisLine={{ stroke: '#E5E7EB' }}
                    tick={{ fontSize: 11, fill: '#6B7280' }}
                    tickLine={false}
                    interval={labelInterval}
                />
                <YAxis
                    axisLine={false}
                    tick={{ fontSize: 11, fill: '#6B7280' }}
                    tickLine={false}
                    domain={[0, 'auto']}
                    ticks={ticks}
                    label={YAxislabel ? { value: YAxislabel, angle: -90, position: 'insideLeft', style: { textAnchor: 'middle', fill: '#6B7280', fontSize: 12 } } : undefined}
                />
                <Tooltip content={<CustomTooltip />} />
                <Area
                    type="monotone"
                    dataKey="value"
                    stroke="#FF6B35"
                    strokeWidth={2}
                    fill="url(#colorGradient)"
                    dot={false}
                />
            </AreaChart>
        </ResponsiveContainer>
    );
};

export default CustomLineChart;