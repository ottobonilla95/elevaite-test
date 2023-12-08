"use client";
import * as React from "react";
import { ColorContext } from "../../contexts";
import Link from "next/link";
import { useRouter } from "next/navigation";
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

export function Card({ icon, title, subtitle, description, ...props }: CardProps) {
  const colors = React.useContext(ColorContext);
  const [btnHover, setBtnHover] = React.useState(false);
  const [cardHover, setCardHover] = React.useState(false);
  const [focus, setFocus] = React.useState(false);
  const router = useRouter();
  React.useEffect(() => console.log("LINK: " + props.link, []));

  const handleClick = (e: React.MouseEvent) => {
    console.log(props.link);
    console.log(router);

    e.preventDefault();
    props.link && router.push(props.link);
  };

  return (
    // <Link
    //   href={props.link || ""}
    //   prefetch={false}
    //   style={{ pointerEvents: props.link ? "auto" : "none", width: "100%" }}
    // >
    <a
      href={props.link}
      target="_blank"
      rel="noopener noreferrer"
      className="cardContainer"
      style={{
        borderTop: props.withHighlight ? "1px solid " + colors.highlight : "",
        cursor: props.link && cardHover ? "pointer" : "auto",
      }}
      id={props.id}
      onFocus={() => setFocus(true)}
      onBlur={() => setFocus(false)}
      // tabIndex={props.link ? 0 : -1}
      // onClick={(e) => handleClick(e)}
      onMouseEnter={() => setCardHover(true)}
      onMouseLeave={() => setCardHover(false)}
    >
      <div
        className="card"
        style={{
          background: colors?.primary,
          borderColor: focus ? colors.highlight : colors?.borderColor,
          borderWidth: focus ? "2px" : "1px",
        }}
      >
        <div className="cardHeader">
          <div className="cardHeaderText">
            <img className="cardIcon" src={icon} width={40} height={40} alt={props.iconAlt} />
            <div className="cardTitle" style={{ color: colors?.text }}>
              {title}
            </div>
          </div>
          {subtitle ? (
            <div className="cardSubtitle" style={{ color: colors?.highlight, background: colors?.tertiary }}>
              <svg width="5" height="4" viewBox="0 0 5 4" fill="none" xmlns="http://www.w3.org/2000/svg">
                <circle cx="2.33325" cy="2" r="2" fill="currentColor" />
              </svg>
              {subtitle}
            </div>
          ) : (
            <></>
          )}
        </div>
        <div className="cardDescription" style={{ color: colors?.text }}>
          {description}
        </div>
        {props.btnLabel ? (
          <button
            className="cardBtn"
            id={props.id ? props.id + "Btn" : ""}
            style={{
              color: colors?.text,
              background: btnHover ? colors.hoverColor : colors.primary,
              borderColor: colors.borderColor,
            }}
            onMouseEnter={() => setBtnHover(true)}
            onFocus={() => setBtnHover(true)}
            onBlur={() => setBtnHover(false)}
            onMouseLeave={() => setBtnHover(false)}
          >
            {props.btnLabel}
            <svg
              width="16"
              height="16"
              viewBox="0 0 16 16"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
              style={{ color: colors.text }}
            >
              <path
                d="M6 12L10 8L6 4"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </button>
        ) : (
          <></>
        )}
      </div>
    </a>
    // </Link>
  );
}

export default Card;
