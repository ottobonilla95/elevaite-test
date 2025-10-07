import React from 'react';
import './HeatMapChart.scss';

interface HeatmapProps {
    customers: string[];
    machineTypes: string[];
    heatmapData: number[][];
}

const getColor = (value: number) => {
    if (value === 0) return 'transparent';
    if (value >= 2800) return '#B14D1D'; // Darkest brown
    if (value >= 2100) return '#CC5500'; // Dark brown-orange
    if (value >= 1667) return '#E65C00'; // Dark orange
    if (value >= 1500) return '#FF6600'; // Orange
    if (value >= 1000) return '#FF8533'; // Medium orange
    if (value >= 500) return '#FFA366'; // Light orange
    if (value >= 100) return '#FFC299'; // Lighter orange
    if (value >= 50) return '#FFD9C4'; // Very light orange
    return '#FFE5D9'; // Lightest orange
};

const HeatmapChart: React.FC<HeatmapProps> = ({ customers, machineTypes, heatmapData }) => {
    return (
        <div className="heatmap-chart">
            <table className="heatmap-table">
                <thead>
                    <tr>
                        <th className="corner-cell"></th>
                        {machineTypes.map((type, idx) => (
                            <th key={idx} className="machine-type-header">{type}</th>
                        ))}
                    </tr>
                </thead>
                <tbody>
                    {customers.map((customer, rowIndex) => (
                        <tr key={rowIndex}>
                            <td className="customer-name">{customer}</td>
                            {heatmapData[rowIndex].map((value, colIndex) => (
                                <td
                                    key={colIndex}
                                    className="heatmap-cell"
                                    style={{
                                        backgroundColor: getColor(value),
                                        color: value >= 2100 ? '#FFFFFF' : '#333333'
                                    }}
                                >
                                    {value > 0 ? value.toLocaleString() : ''}
                                </td>
                            ))}
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
};

export default HeatmapChart;