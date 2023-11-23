import * as React from "react";
import "./workshopcard.css";

interface WorkshopCardProps {
  icon: string;
  iconAlt: string;
  title: string;
  subtitle: string;
  description: string;
  width?: number;
  height?: number;
}

export function WorkshopCard({ icon, title, subtitle, description, ...props }: WorkshopCardProps) {
  return (
    <div className="card">
      <div className="cardHeader">
        <img className="cardIcon" src={icon} width={40} height={40} alt={props.iconAlt} />
        <div className="cardHeaderText">
          <div className="cardTitle">{title}</div>
          <div className="cardSubtitle">{subtitle}</div>
        </div>
      </div>
      <div className="cardDescription">{description}</div>
    </div>
  );
}

export default WorkshopCard;
