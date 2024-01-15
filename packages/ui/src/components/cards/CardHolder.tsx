"use client";
import React, { Children, useState } from "react";
import SVGChevron from "../icons/elevaite/svgChevron";
import "./CardHolder.scss";


export interface CardHolderProps {
  title: string;
  children?: React.ReactNode;
}

export function CardHolder(props: CardHolderProps): JSX.Element {
  const [closed, setClosed] = useState(false);

  return (
    <div className="card-drawer-container">
      <div className="card-drawer-header">
        <button 
          className={[
            "card-drawer-button",
            closed ? "closed" : undefined,
          ].filter(Boolean).join(" ")}
          onClick={() => { setClosed(!closed); }}
          type="button"
        >
          <SVGChevron/>
          {props.title}
        </button>
        <div className="item-count">
          {Children.count(props.children)}
        </div>
      </div>
      <div className={[
        "card-drawer-accordion",
        closed ? "closed" : undefined,
      ].filter(Boolean).join(" ")}>
        <div className="card-drawer-content">
          {props.children}
        </div>
      </div>
    </div>
  );
}
