"use client";
import * as React from "react";
import { ColorContext } from "../../contexts";
import "./Card.css";

export interface CardProps {
  icon: string;
  iconAlt: string;
  title: string;
  subtitle?: string;
  description: string;
  width?: number;
  height?: number;
  btnLabel?: string;
  withHighlight?: boolean;
  id?: string;
  link?: string;
}

export function Card({ icon, title, subtitle, description, ...props }: CardProps): JSX.Element {
  const colors = React.useContext(ColorContext);
  const [btnHover, setBtnHover] = React.useState(false);
  const [cardHover, setCardHover] = React.useState(false);
  const [focus, setFocus] = React.useState(false);

  return (
    <div
      className="cardContainer"
      id={props.id}
      onBlur={() => {
        setFocus(false);
      }}
      onFocus={() => {
        setFocus(true);
      }}
      onMouseEnter={() => {
        setCardHover(true);
      }}
      onMouseLeave={() => {
        setCardHover(false);
      }}
      style={{
        borderTop: props.withHighlight ? `1px solid ${colors.highlight}` : "",
        cursor: props.link && cardHover ? "pointer" : "auto",
      }}
    >
      <div
        className="card"
        style={{
          background: colors.primary,
          borderColor: focus ? colors.highlight : colors.borderColor,
          borderWidth: focus ? "2px" : "1px",
        }}
      >
        <div className="cardHeader">
          <div className="cardHeaderText">
            <img alt={props.iconAlt} className="cardIcon" height={40} src={icon} width={40} />
            <div className="cardTitle" style={{ color: colors.text }}>
              {title}
            </div>
          </div>
          {subtitle ? (
            <div className="cardSubtitle" style={{ color: colors.highlight, background: colors.tertiary }}>
              <svg fill="none" height="4" viewBox="0 0 5 4" width="5" xmlns="http://www.w3.org/2000/svg">
                <circle cx="2.33325" cy="2" fill="currentColor" r="2" />
              </svg>
              {subtitle}
            </div>
          ) : null}
        </div>
        <div className="cardDescription" style={{ color: colors.text }}>
          {description}
        </div>
        {props.btnLabel ? (
          <button
            className="cardBtn"
            id={props.id ? `${props.id}Btn` : ""}
            onBlur={() => {
              setBtnHover(false);
            }}
            onFocus={() => {
              setBtnHover(true);
            }}
            onMouseEnter={() => {
              setBtnHover(true);
            }}
            onMouseLeave={() => {
              setBtnHover(false);
            }}
            style={{
              color: colors.text,
              background: btnHover ? colors.hoverColor : colors.primary,
              borderColor: colors.borderColor,
            }}
            type="button"
          >
            {props.btnLabel}
            <svg
              fill="none"
              height="16"
              style={{ color: colors.text }}
              viewBox="0 0 16 16"
              width="16"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path
                d="M6 12L10 8L6 4"
                stroke="currentColor"
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth="1.5"
              />
            </svg>
          </button>
        ) : null}
      </div>
    </div>
  );
}

export default Card;
