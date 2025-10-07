import React from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';

interface PieChartData {
    name: string;
    value: number;
    color?: string;
    count?: number;
    [key: string]: any;
}

interface CustomPieChartProps {
    data: PieChartData[];
    dollorValue?: boolean;
}

const CustomPieChart: React.FC<CustomPieChartProps> = ({
    data,
    dollorValue = false
}) => {
    if (!data || data.length === 0) {
        return (
            <div style={{
                width: '100%',
                height: '280px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#666',
                fontSize: '14px'
            }}>
                No data available
            </div>
        );
    }

    const CustomTooltip = ({ active, payload }: any) => {
        if (active && payload && payload.length) {
            const data = payload[0].payload;
            return (
                <div style={{
                    backgroundColor: 'white',
                    padding: '8px 12px',
                    border: '1px solid #e0e0e0',
                    borderRadius: '4px',
                    boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
                    fontSize: '13px'
                }}>
                    <p style={{ margin: 0, fontWeight: 'bold' }}>{data.name}</p>
                    <p style={{ margin: '4px 0 0 0', color: '#666' }}>
                        {dollorValue ? `$${data.value.toLocaleString()}` : `${data.value}%`}
                        {data.count && ` (${data.count.toLocaleString()})`}
                    </p>
                </div>
            );
        }
        return null;
    };

    const renderCustomLegend = (props: any) => {
        const { payload } = props;
        if (!payload) return null;

        return (
            <div style={{
                display: 'flex',
                flexWrap: 'wrap',
                justifyContent: 'center',
                gap: '12px',
                marginTop: '16px',
                fontSize: '12px'
            }}>
                {payload.map((entry: any, index: number) => (
                    <div
                        key={index}
                        style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: '6px'
                        }}
                    >
                        <div
                            style={{
                                width: '12px',
                                height: '12px',
                                backgroundColor: entry.color,
                                borderRadius: '2px',
                                flexShrink: 0
                            }}
                        />
                        <span style={{
                            color: '#333',
                            whiteSpace: 'nowrap',
                            maxWidth: '120px',
                            overflow: 'hidden',
                            textOverflow: 'ellipsis'
                        }}>
                            {entry.value}
                        </span>
                    </div>
                ))}
            </div>
        );
    };

    return (
        <div style={{
            width: '100%',
            height: '100%',
            minHeight: '280px',
            display: 'flex',
            flexDirection: 'column'
        }}>
            <div style={{
                width: '100%',
                height: '220px',
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center'
            }}>
                <PieChart width={280} height={200}>
                    <Pie
                        data={data}
                        cx={140}
                        cy={100}
                        innerRadius={45}
                        outerRadius={85}
                        paddingAngle={2}
                        dataKey="value"
                    >
                        {data.map((entry, index) => (
                            <Cell
                                key={`cell-${index}`}
                                fill={entry.color || `hsl(${index * 45}, 70%, 60%)`}
                                stroke="white"
                                strokeWidth={1}
                            />
                        ))}
                    </Pie>
                    <Tooltip content={<CustomTooltip />} />
                </PieChart>
            </div>

            {/* Custom legend */}
            <div style={{ flex: 1, display: 'flex', alignItems: 'flex-start' }}>
                {renderCustomLegend({
                    payload: data.map((item, index) => ({
                        value: item.name,
                        color: item.color || `hsl(${index * 45}, 70%, 60%)`
                    }))
                })}
            </div>
        </div>
    );
};

export default CustomPieChart;

