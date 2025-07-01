"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { CommonButton, Logos } from "..";
import SVGChevron from "../icons/elevaite/svgChevron";
import "./Card.scss";

export interface CardProps {
  icon: string;
  iconAlt?: string;
  title: string;
  subtitle?: string;
  description: string;
  width?: number;
  height?: number;
  miscLabel?: string;
  btnLabel?: string;
  url?: string;
  externalUrl?: string;
  openInNewTab?: boolean;
  id?: string | number;
  link?: string;
}

export function Card({
  icon,
  title,
  subtitle,
  description,
  ...props
}: CardProps): JSX.Element {
  const pathname = usePathname();
  const [iconElement, setIconElement] = useState<React.ReactNode>(null);
  const [formattedUrl, setFormattedUrl] = useState("/");

  useEffect(() => {
    setIconElement(getIconElement(props.id, icon, props.iconAlt));
  }, [props.id, icon]);

  useEffect(() => {
    setFormattedUrl(
      props.externalUrl
        ? props.externalUrl
        : props.url
          ? pathname + props.url + addIdParameter()
          : "/"
    );
  }, [props.url, props.externalUrl]);

  function addIdParameter(): string {
    if (!props.id) return "";
    const parameters = new URLSearchParams();
    parameters.set("id", props.id.toString());
    return `?${parameters.toString()}`;
  }

  return (
    <div
      className={["card-container", props.link ? "with-link" : undefined]
        .filter(Boolean)
        .join(" ")}
      id={props.id?.toString()}
    >
      <div className="card">
        <div className="card-header">
          <div className="card-header-title">
            {iconElement}
            <div className="card-header-label">{title}</div>
          </div>
          {/* {subtitle ? 
            <div className="card-header-subtitle">
              <SVGDot />
              {subtitle}
            </div>
          : null} */}
        </div>
        <div className="card-description">{description}</div>
        {props.miscLabel ? (
          <span className="card-misc-label">{props.miscLabel}</span>
        ) : null}
        {!props.btnLabel ? undefined : (
          <div className="card-button-container">
            <Link
              href={formattedUrl}
              rel={props.openInNewTab ? "noopener noreferrer" : undefined}
              target={props.openInNewTab ? "_blank" : undefined}
            >
              <CommonButton className="card-button">
                {props.btnLabel}
                <SVGChevron type="right" />
              </CommonButton>
            </Link>
          </div>
        )}
      </div>
    </div>
  );
}

export default Card;

function getIconElement(
  id?: string | number,
  icon?: string,
  iconAlt?: string
): React.ReactNode {
  if (icon)
    return (
      <img src={icon} alt={iconAlt ?? "logo"} className="card-header-icon" />
    );
  switch (id?.toString()) {
    case "1":
      return <Logos.Aws className="card-header-icon" />;
    case "2":
      return <Logos.Preprocess className="card-header-icon" />;
    case "LocalApp_1":
      return <Logos.Jupyter className="card-header-icon" />;
    case "LocalApp_2":
      return (
        <svg
          className="card-header-icon"
          width="32"
          height="32"
          viewBox="0 0 32 32"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          <g clipPath="url(#clip0_1215_3468)">
            <ellipse
              cx="8.53988"
              cy="11.3908"
              rx="8.17305"
              ry="12.532"
              transform="rotate(27.5347 8.53988 11.3908)"
              fill="#D9D9D9"
              fillOpacity="0.3"
            />
            <path
              d="M23.9993 17.333V14.6663H29.3327V17.333H23.9993ZM25.5993 26.6663L21.3327 23.4663L22.9327 21.333L27.1993 24.533L25.5993 26.6663ZM22.9327 10.6663L21.3327 8.53301L25.5993 5.33301L27.1993 7.46634L22.9327 10.6663ZM6.66602 25.333V19.9997H2.66602V11.9997H10.666L17.3327 7.99967V23.9997L10.666 19.9997H9.33268V25.333H6.66602ZM18.666 20.4663V11.533C19.266 12.0663 19.7496 12.7166 20.1167 13.4837C20.4838 14.2508 20.6669 15.0895 20.666 15.9997C20.666 16.9108 20.4825 17.7499 20.1153 18.517C19.7482 19.2841 19.2651 19.9339 18.666 20.4663Z"
              fill="#F46F22"
            />
            <path
              d="M3.5 9.5V5.83333C3.5 5.3471 3.69566 4.88079 4.04394 4.53697C4.39223 4.19315 4.8646 4 5.35714 4C5.84969 4 6.32206 4.19315 6.67034 4.53697C7.01862 4.88079 7.21429 5.3471 7.21429 5.83333V9.5M3.5 7.66667H7.21429M10 4V9.5"
              stroke="#0066BE"
              strokeWidth="1.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </g>
          <defs>
            <clipPath id="clip0_1215_3468">
              <rect width="32" height="32" fill="white" />
            </clipPath>
          </defs>
        </svg>
      );
    default:
      return null;
  }
}
