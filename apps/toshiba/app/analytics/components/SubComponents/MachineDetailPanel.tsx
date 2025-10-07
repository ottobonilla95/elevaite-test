import React from "react";
import { FaCog } from "react-icons/fa";
import "./MachineDetailPanel.scss";
import { MachineDetail } from "../../lib/types";

interface MachineDetailPanelProps {
    data: MachineDetail[];
}

const MachineDetailPanel: React.FC<MachineDetailPanelProps> = ({ data = [] }) => {

    const hasRealData = data && data.length > 0;

    if (!hasRealData) {
        return (
            <div className="machine-detail-panel">
                <div className="no-data-message">
                    No machine details available
                </div>
            </div>
        );
    }


    const displayData = data.slice(0, 8).map(item => ({
        id: item.machine_type,
        cost: `$${item.total_cost.toLocaleString(undefined, {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        })}`,
        time: (() => {
            const days = item.avg_resolution_time || 0;
            const hours = Math.floor(days * 24);
            const minutes = Math.round((days * 24 * 60) % 60);
            return `${hours}h${minutes}m`;
        })()
    }));

    return (
        <div className="machine-detail-panel">
            <div className="machine-cards">
                {displayData.map((machine) => (
                    <div className="machine-card" key={machine.id}>
                        <div className="machine-id">
                            <FaCog className="icon" />
                            <span>{machine.id}</span>
                        </div>
                        <div className="metrics">
                            <div className="metric">
                                <div className="metric-label">Total Cost of Parts</div>
                                <div className="metric-value">{machine.cost}</div>
                            </div>
                            <div className="metric">
                                <div className="metric-label">Avg SR Resolution Time</div>
                                <div className="metric-value">{machine.time}</div>
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default MachineDetailPanel;