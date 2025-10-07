import React from 'react';
import "./StatCard.scss";

type StatCardProps = {
    label: string;
    value: string;
    trend?: string;
    icon: React.ReactNode;
};

const StatCard: React.FC<StatCardProps> = ({ icon, label, value, trend }) => {

    const trendClass = trend?.startsWith("-") ? "negative" : trend?.startsWith("+") ? "positive" : "";

    return (
        <div className='stat-card'>
            <div className='stat-content'>
                <div className="stat-icon"> {icon}</div>
                <div className="stat-details">
                    <h4>{label}</h4>
                    <h2>{value}</h2>
                    <p className={trendClass}>{trend}</p>
                </div>

            </div>
        </div>
    );
};

export default StatCard;