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

export function Searchbar({ handleInput, ...props }: SearchBarProps) {
  const [showResults, setShowResults] = useState(false);

  const handleChange = (value: string) => {
    handleInput(value);
  };

  const handleResultClick = (targetId?: string) => {
    console.log(props.isJump);
    console.log(targetId);

    if (props.isJump && targetId !== undefined) {
      const element = document.getElementById(targetId + "Btn");
      element?.focus();
    }
    setShowResults(false);
  };

  const colors = useContext(ColorContext);
  return (
    <>
      <div
        className="searchbarContainer"
        style={{ width: props.width }}
        onFocus={() => setShowResults(true)}
        onBlur={() =>
          setTimeout(() => {
            setShowResults(false);
          }, 100)
        }
      >
        <div className="searchbar" style={{ borderColor: colors.borderColor, background: colors.background }}>
          <svg
            width="20"
            height="20"
            viewBox="0 0 20 20"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
            style={{ color: colors.icon }}
          >
            <path
              d="M17.5 17.5L13.875 13.875M15.8333 9.16667C15.8333 12.8486 12.8486 15.8333 9.16667 15.8333C5.48477 15.8333 2.5 12.8486 2.5 9.16667C2.5 5.48477 5.48477 2.5 9.16667 2.5C12.8486 2.5 15.8333 5.48477 15.8333 9.16667Z"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
          <input
            type="search"
            onChange={(e) => handleChange(e.target.value)}
            placeholder="Find answers"
            style={{ background: colors.background, color: colors.text }}
          />
          {/* <label className="searchHotKeyHint">
            {navigator.platform.toUpperCase().indexOf("MAC") >= 0 ? "⌘" : "Ctrl"}+F
          </label> */}
        </div>
        {showResults ? (
          <SearchResults
            results={props.results}
            handleResultClick={handleResultClick}
            isJump={props.isJump}
            topOffset={props.resultsTopOffset}
          />
        ) : (
          <></>
        )}
      </div>
    </>
  );
}
