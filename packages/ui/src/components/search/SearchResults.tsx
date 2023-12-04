"use client";
import { useContext, useState } from "react";
import { ColorContext } from "../../ColorContext";
import Link from "next/link";
import "./SearchResults.css";

interface SearchResultsProps {
  results: { key: string; link: string; label: string }[];
}

export function SearchResults({ results }: SearchResultsProps) {
  const [hover, setHover] = useState("");
  const colors = useContext(ColorContext);

  return (
    <>
      {results?.length > 0 ? (
        <div
          className="searchResultContainer"
          style={{ borderColor: colors.borderColor, background: colors.background }}
        >
          {results.map((res) => (
            <Link
              href={res.link}
              className="searchResult"
              key={res.key}
              style={{
                color: hover === res.key ? colors.primary : colors.text,
                background: hover === res.key ? colors.highlight : "",
              }}
              onMouseEnter={() => setHover(res.key)}
              onMouseLeave={() => setHover("")}
            >
              {res.label}
            </Link>
          ))}
        </div>
      ) : (
        <></>
      )}{" "}
    </>
  );
}
