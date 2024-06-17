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

export function Card({ icon, title, subtitle, description, ...props }: CardProps): JSX.Element {
  const pathname = usePathname();
  const [iconElement, setIconElement] = useState<React.ReactNode>(null);
  const [formattedUrl, setFormattedUrl] = useState("/");


  useEffect(() => {
    setIconElement(getIconElement(props.id, icon, props.iconAlt));
  }, [props.id, icon]);

  useEffect(() => {
    setFormattedUrl(
      props.externalUrl ? props.externalUrl :
      props.url ? pathname + props.url + addIdParameter() :
      "/"
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
      className={[
        "card-container",
        props.link ? "with-link" : undefined,
      ].filter(Boolean).join(" ")}
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
        {props.miscLabel ? 
          <span className="card-misc-label">{props.miscLabel}</span>
        : null}
        {!props.btnLabel ? undefined :
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
        }
      </div>
    </div>
  );
}

export default Card;




function getIconElement(id?: string | number, icon?: string, iconAlt?: string): React.ReactNode {
  if (icon) return <img src={icon} alt={iconAlt ?? "logo"} className="card-header-icon" />
  switch (id?.toString()) {
    case "1": return <Logos.Aws className="card-header-icon"/>;
    case "2": return <Logos.Preprocess className="card-header-icon"/>;
    case "LocalApp_1": return <Logos.Jupyter className="card-header-icon"/>;
    default: return null;
  }
}