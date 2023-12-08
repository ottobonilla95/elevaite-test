"use client";
import type { SVGProps } from "react";
import React, { useContext, useState } from "react";
import { ColorContext } from "../../contexts";
import "./CardHolder.css";

export interface CardHolderProps {
  title: string;
  children?: React.ReactNode;
}

export function CardHolder(props: CardHolderProps): JSX.Element {
  const colors = useContext(ColorContext);
  const [hidden, setHidden] = useState(false);

  return (
    <div className="cardHolderContainer" style={{ borderColor: colors.borderColor, background: colors.primary }}>
      <div
        className="cardHolderTitle"
        style={{ borderBottom: hidden ? "" : `1px solid ${colors.borderColor}`, color: colors.text }}
      >
        <button
          className="cardHolderTitleBtn"
          onClick={() => {
            setHidden(!hidden);
          }}
          type="button"
        >
          {hidden ? <ChevronRight color={colors.text} /> : <ChevronBottom color={colors.text} />}
          {props.title}
        </button>
        {/* <div className="cardHolderTitleIcons">
          <Clipboard color={colors.icon} />
          <Burger color={colors.icon} />
        </div> */}
      </div>
      <div className="cardHolderContent" style={{ display: hidden ? "none" : "grid" }}>
        {props.children}
      </div>
    </div>
  );
}

function ChevronBottom(props: SVGProps<SVGSVGElement>): JSX.Element {
  return (
    <svg fill="none" height={17} width={16} xmlns="http://www.w3.org/2000/svg" {...props}>
      <path d="m4 6.5 4 4 4-4" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} />
    </svg>
  );
}
function ChevronRight(props: SVGProps<SVGSVGElement>): JSX.Element {
  return (
    <svg fill="none" height={16} width={16} xmlns="http://www.w3.org/2000/svg" {...props}>
      <path d="m6 12 4-4-4-4" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} />
    </svg>
  );
}

// eslint-disable-next-line @typescript-eslint/no-unused-vars -- Might be re-added
function Clipboard(props: SVGProps<SVGSVGElement>): JSX.Element {
  return (
    <svg fill="none" height={25} width={24} xmlns="http://www.w3.org/2000/svg" {...props}>
      <path
        d="M14 2.77V6.9c0 .56 0 .84.109 1.054a1 1 0 0 0 .437.437c.214.11.494.11 1.054.11h4.13M16 13.5H8m8 4H8m2-8H8m6-7H8.8c-1.68 0-2.52 0-3.162.327a3 3 0 0 0-1.311 1.311C4 4.78 4 5.62 4 7.3v10.4c0 1.68 0 2.52.327 3.162a3 3 0 0 0 1.311 1.311c.642.327 1.482.327 3.162.327h6.4c1.68 0 2.52 0 3.162-.327a3 3 0 0 0 1.311-1.311C20 20.22 20 19.38 20 17.7V8.5l-6-6Z"
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
      />
    </svg>
  );
}

// eslint-disable-next-line @typescript-eslint/no-unused-vars -- Might be re-added
function Burger(props: SVGProps<SVGSVGElement>): JSX.Element {
  return (
    <svg fill="currentColor" height={25} width={24} xmlns="http://www.w3.org/2000/svg" {...props}>
      <path d="M3.2 18.5h18v-1.933h-18V18.5Zm0-4.833h18v-1.934h-18v1.934Zm0-6.767v1.933h18V6.9h-18Z" fill="#64748B" />
    </svg>
  );
}
