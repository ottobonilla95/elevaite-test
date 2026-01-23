"use client";
import type { JSX } from "react";
import { useContext, useState } from "react";
import Link from "next/link";
import { ColorContext } from "../../contexts";
import "./SearchResults.css";

interface SearchResultsProps {
  results: { key: string; link: string; label: string }[];
  handleResultClick: (targetId?: string) => void;
  topOffset: string;
  isJump?: boolean;
}

export function SearchResults({ results, handleResultClick, topOffset, ...props }: SearchResultsProps): JSX.Element {
  const [hover, setHover] = useState("");
  const colors = useContext(ColorContext);

  return (
    <div
      className="searchResultContainer"
      style={{ borderColor: colors.borderColor, background: colors.background, top: topOffset }}
    >
      {results.map((res) => (
        <Link
          className="searchResult"
          href={res.link}
          key={res.key}
          onClick={() => {
            handleResultClick(res.key);
          }}
          onMouseEnter={() => {
            setHover(res.key);
          }}
          onMouseLeave={() => {
            setHover("");
          }}
          replace={props.isJump}
          style={{
            color: hover === res.key ? colors.primary : colors.text,
            background: hover === res.key ? colors.highlight : "",
          }}
        >
          {res.label}
        </Link>
      ))}
    </div>
  );
}
