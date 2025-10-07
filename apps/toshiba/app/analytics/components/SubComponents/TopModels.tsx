
import React from 'react';
import { Treemap, Tooltip, ResponsiveContainer } from 'recharts';

interface TopModelData {
    model: string;
    count: number;
}

interface TopModelsProps {
    data: TopModelData[];
}

const COLORS = [
    '#1B7C5D',
    '#259D6F',
    '#2DB884',
    '#5CE4B7',
    '#9EDAC6',
    '#5CE4B7',
    '#B3F0DD',
    '#A3E9D1',
    '#A3E9D1',
    '#ADE7D4',

];


// Custom content renderer for the treemap cells matching Figma exactly
const CustomContent = ({ root, depth, x, y, width, height, index, colors, name, value }: any) => {
    return (
        <g>
            <rect
                x={x}
                y={y}
                width={width}
                height={height}
                style={{
                    fill: colors[index % colors.length],
                    stroke: '#fff',
                    strokeWidth: 3,
                    strokeOpacity: 1,
                }}
            />
            {width > 40 && height > 40 && (
                <>
                    <text
                        x={x + width / 2}
                        y={y + height / 2 - 12}
                        textAnchor="middle"
                        fill="#fff"
                        fontSize={width > 100 ? 20 : 20}
                        fontWeight="100"
                        style={{ fontFamily: '-apple-system, BlinkMacSystemFont, sans-serif' }}
                    >
                        {name}
                    </text>
                    <text
                        x={x + width / 2}
                        y={y + height / 2 + 15}
                        textAnchor="middle"
                        fill="#fff"
                        fontSize={width > 100 ? 15 : 18}
                        fontWeight="50"
                        style={{ fontFamily: '-apple-system, BlinkMacSystemFont, sans-serif' }}
                    >
                        {value}
                    </text>
                </>
            )}
        </g>
    );
};


const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
        return (
            <div style={{
                backgroundColor: 'rgba(255, 255, 255, 0.95)',
                border: '1px solid #e5e5e5',
                borderRadius: '8px',
                padding: '10px 14px',
                boxShadow: '0 2px 8px rgba(0,0,0,0.08)'
            }}>
                <p style={{ margin: 0, fontSize: '14px', fontWeight: 600, color: '#374151' }}>
                    {payload[0].payload.name}
                </p>
                <p style={{ margin: 0, fontSize: '16px', color: '#1B7C5D', fontWeight: 500 }}>
                    {payload[0].value}
                </p>
            </div>
        );
    }
    return null;
};

const TopModels: React.FC<TopModelsProps> = ({ data = [] }) => {
    // Add debug logging
    React.useEffect(() => {
        console.log("TopModels received data:", data);
    }, [data]);

    // Map backend data to format required by Treemap
    const treemapData = data.map(item => ({
        name: item.model,
        size: item.count,
        value: item.count
    }));


    return (
        <div className="top-models" style={{ backgroundColor: '#F9FAFB', borderRadius: '8px', padding: '4px' }}>
            <ResponsiveContainer width="100%" height={280}>
                <Treemap
                    data={treemapData}
                    dataKey="size"
                    aspectRatio={16 / 9}
                    stroke="#fff"
                    content={<CustomContent colors={COLORS} />}
                >
                    <Tooltip content={<CustomTooltip />} />
                </Treemap>
            </ResponsiveContainer>
        </div>
    );
};

export default TopModels;