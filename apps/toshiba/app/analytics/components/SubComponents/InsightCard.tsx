"Use Client"

import React from 'react';
import "./InsightCard.scss";

type InsightCardProps = {
    icon: React.ReactNode;
    title: string;
    value: string | number;
    description: string;
};

const InsightCard: React.FC<InsightCardProps> = ({ icon, title, value, description }) => {
    return (
        <div className='insight-card'>
            <div className='insight-content'>
                <div className="insight-icon"> {icon}</div>
                <div className="insight-details">
                    <h4>{title}</h4>
                    <h2>{value}</h2>
                    <p>{description}</p>
                </div>

            </div>
        </div>
    );
};

export default InsightCard;