"use client";
import SVGChevron from "../icons/elevaite/svgChevron";
import SVGDot from "../icons/elevaite/svgDot";
import "./Card.scss";

export interface CardProps {
  icon: string;
  iconAlt: string;
  title: string;
  subtitle?: string;
  description: string;
  width?: number;
  height?: number;
  miscLabel?: string;
  btnLabel?: string;
  id?: string;
  link?: string;
  altBackground?: boolean;
}

export function Card({ icon, title, subtitle, description, ...props }: CardProps): JSX.Element {

  return (
    <div
      className={[
        "card-container",
        props.link ? "with-link" : undefined,
        props.altBackground ? "alt-background" : undefined,
      ].filter(Boolean).join(" ")}
      id={props.id}
    >
      <div className="card">
        <div className="card-header">
          <div className="card-header-title">
            <img alt={props.iconAlt} className="card-header-icon" src={icon} />
            <div className="card-header-label">{title}</div>
          </div>
          {subtitle ? 
            <div className="card-header-subtitle">
              <SVGDot />
              {subtitle}
            </div>
          : null}
        </div>
        <div className="card-description">{description}</div>
        {props.miscLabel ? 
          <span className="card-misc-label">{props.miscLabel}</span>
        : null}
        {props.btnLabel ? 
          <button
            className="card-button"
            id={props.id ? `${props.id}Btn` : ""} /* <- What's this for? */
            type="button"
          >
            {props.btnLabel}
            <SVGChevron type="right" />
          </button>
        : null}
      </div>
    </div>
  );
}

export default Card;
