"use client";
import { usePathname, useRouter } from "next/navigation";
import { Logos } from "..";
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
  id?: string;
  link?: string;
  altBackground?: boolean;
}

export function Card({ icon, title, subtitle, description, ...props }: CardProps): JSX.Element {
  const router = useRouter();
  const pathname = usePathname();

  function addIdParameter(): string {
    if (!props.id) return "";
    const parameters = new URLSearchParams();
    parameters.set("id", props.id);
    return `?${parameters.toString()}`;
  }

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
            {!icon ? //TODO: Remove testing icons
                props.id == "1" ? <Logos.Aws/> :
                props.id == "2" ? <Logos.Preprocess/>
              : null :
              <img src={icon} alt={props.iconAlt ? props.iconAlt : "logo"} className="card-header-icon" />
            }
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
        {props.btnLabel ? 
          <button
            className="card-button"
            disabled={!props.url}
            id={props.id ? `${props.id}Btn` : ""} /* <- What's this for? */
            onClick={() => { if (props.url) router.push(pathname + props.url + addIdParameter())}}
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
