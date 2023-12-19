"use client";
import { useContext, useState } from "react";
import "./Searchbar.css";
import { ColorContext } from "../../contexts";
import { SearchResults } from "./SearchResults";

interface SearchBarProps {
  handleInput: (term: string) => void;
  results: { key: string; link: string; label: string }[];
  resultsTopOffset: string;
  width?: string;
  isJump?: boolean;
}

export function Searchbar({ handleInput, ...props }: SearchBarProps): JSX.Element {
  const [showResults, setShowResults] = useState(false);

  const handleChange = (value: string): void => {
    handleInput(value);
  };

  const handleResultClick = (targetId?: string): void => {
    if (props.isJump && targetId !== undefined) {
      const card = document.getElementById(targetId);
      if (card) {
        card.focus();
      } else {
        const cardBtn = document.getElementById(`${targetId}Btn`);
        cardBtn && cardBtn.focus();
      }
    }
    setShowResults(false);
  };

  const colors = useContext(ColorContext);
  return (
    <div
      className="searchbarContainer"
      onBlur={() =>
        setTimeout(() => {
          setShowResults(false);
        }, 100)
      }
      onFocus={() => {
        setShowResults(true);
      }}
      style={{ width: props.width }}
    >
      <div className="searchbar" style={{ borderColor: colors.borderColor, background: colors.background }}>
        <svg
          fill="none"
          height="20"
          style={{ color: colors.icon }}
          viewBox="0 0 20 20"
          width="20"
          xmlns="http://www.w3.org/2000/svg"
        >
          <path
            d="M17.5 17.5L13.875 13.875M15.8333 9.16667C15.8333 12.8486 12.8486 15.8333 9.16667 15.8333C5.48477 15.8333 2.5 12.8486 2.5 9.16667C2.5 5.48477 5.48477 2.5 9.16667 2.5C12.8486 2.5 15.8333 5.48477 15.8333 9.16667Z"
            stroke="currentColor"
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth="2"
          />
        </svg>
        <input
          onChange={(e) => {
            handleChange(e.target.value);
          }}
          placeholder="Find answers"
          style={{ background: colors.background, color: colors.text }}
          type="search"
        />
        {/* <label className="searchHotKeyHint">
            {navigator.platform.toUpperCase().indexOf("MAC") >= 0 ? "⌘" : "Ctrl"}+F
          </label> */}
      </div>
      {showResults ? (
        <SearchResults
          handleResultClick={handleResultClick}
          isJump={props.isJump}
          results={props.results}
          topOffset={props.resultsTopOffset}
        />
      ) : null}
    </div>
  );
}
