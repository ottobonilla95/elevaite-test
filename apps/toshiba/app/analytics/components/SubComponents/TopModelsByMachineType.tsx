import React from 'react';
import './TopModelsByMachineType.scss';

interface TopModelsByMachineTypeProps {
    data: Array<{
        machineType: string;
        models: Array<{
            model: string;
            count: number;
        }>;
    }>;
}

const TopModelsByMachineType: React.FC<TopModelsByMachineTypeProps> = ({ data }) => {
    console.log("🔍 TopModelsByMachineType received data:", data);
    console.log("🔍 Data type:", typeof data);
    console.log("🔍 Is array:", Array.isArray(data));
    console.log("🔍 Data length:", data?.length);

    if (!data || data.length === 0) {
        console.log("❌ No data available in TopModelsByMachineType");
        return (
            <div className="top-models-container">
                <div className="no-data">No machine models data available</div>
            </div>
        );
    }

    return (
        <div className="top-models-container">
            <div className="machine-types-grid">
                {data.map((machineType, index) => {
                    console.log(`🔍 Rendering machine type ${index}:`, machineType);
                    return (
                        <div key={machineType.machineType} className="machine-type-card">
                            <div className="machine-type-header">
                                <h4>{machineType.machineType}</h4>
                            </div>
                            <div className="models-list">
                                {machineType.models.map((model, modelIndex) => {
                                    console.log(`🔍 Rendering model ${modelIndex}:`, model);
                                    return (
                                        <div key={modelIndex} className="model-item">
                                            <span className="model-name">{model.model}</span>
                                            <span className="model-count">{model.count} SRs</span>
                                        </div>
                                    );
                                })}
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
};

export default TopModelsByMachineType;