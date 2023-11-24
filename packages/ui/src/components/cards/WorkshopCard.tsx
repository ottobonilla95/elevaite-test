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
    <div className="cardHolder">
      <div className="card">
        <div className="cardHeader">
          <div className="cardHeaderText">
            <img className="cardIcon" src={icon} width={40} height={40} alt={props.iconAlt} />
            <div className="cardTitle">{title}</div>
          </div>
          <div className="cardSubtitle">
            <svg width="5" height="4" viewBox="0 0 5 4" fill="none" xmlns="http://www.w3.org/2000/svg">
              <circle cx="2.33325" cy="2" r="2" fill="#E75F33" />
            </svg>
            {subtitle}
          </div>
        </div>
        <div className="cardDescription">{description}</div>
        <button className="cardBtn">
          Open
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M6 12L10 8L6 4" stroke="white" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" />
          </svg>{" "}
        </button>
      </div>
    </div>
  );
}

export default WorkshopCard;
