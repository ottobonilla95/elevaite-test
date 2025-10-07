import React from "react";

import './HighlightCard.scss'

interface HighlightCardProps {
    title: string;
    subtitle: string;
    value: string;
    footer: string | React.ReactNode;
    bgColor?: string;
}

const HighlightCard: React.FC<HighlightCardProps> = ({ title, subtitle, value, footer }) => {
    return (
        <div className="highlight-container">
            <div className="highlight-header">{title}</div>
            <div className="highlight-tab">
                <div className="subtitle">{subtitle}</div>
                <div className="value">{value}</div>
                <div className="footer">{footer}</div>
            </div>
        </div>
    );
};

export default HighlightCard;
