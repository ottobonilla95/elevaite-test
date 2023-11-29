"use client";
import * as React from "react";
import { ColorContext } from "../../ColorContext";
import "./WorkbenchCard.css";

export interface WorkbenchCardProps {
  icon: string;
  iconAlt: string;
  title: string;
  subtitle: string;
  description: string;
  width?: number;
  height?: number;
}

export function WorkbenchCard({ icon, title, subtitle, description, ...props }: WorkbenchCardProps) {
  const colors = React.useContext(ColorContext);
  const [hover, setHover] = React.useState(false);

  return (
    <div className="cardHolder" style={{ borderTopColor: colors?.highlight }}>
      <div className="card" style={{ background: colors?.primary, borderColor: colors?.secondary }}>
        <div className="cardHeader">
          <div className="cardHeaderText">
            <img className="cardIcon" src={icon} width={40} height={40} alt={props.iconAlt} />
            <div className="cardTitle" style={{ color: colors?.text }}>
              {title}
            </div>
          </div>
          <div className="cardSubtitle" style={{ color: colors?.highlight, background: colors?.tertiary }}>
            <svg width="5" height="4" viewBox="0 0 5 4" fill="none" xmlns="http://www.w3.org/2000/svg">
              <circle cx="2.33325" cy="2" r="2" fill="#E75F33" />
            </svg>
            {subtitle}
          </div>
        </div>
        <div className="cardDescription" style={{ color: colors?.text }}>
          {description}
        </div>
        <button
          className="cardBtn"
          style={{ color: colors?.text, background: hover ? colors.hoverColor : colors.primary }}
          onMouseEnter={() => setHover(true)}
          onFocus={() => setHover(true)}
          onMouseLeave={() => setHover(false)}
        >
          Open
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M6 12L10 8L6 4" stroke="white" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </button>
      </div>
    </div>
  );
}

export default WorkbenchCard;
