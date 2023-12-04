"use client";
import { useContext, useState } from "react";
import "./Searchbar.css";
import { ColorContext } from "../../ColorContext";
import { SearchResults } from "./SearchResults";

interface SearchBarProps {
  handleInput: (term: string) => void;
  results: { key: string; link: string; label: string }[];
  width?: string;
}

export function Searchbar({ handleInput, ...props }: SearchBarProps) {
  const [input, setInput] = useState("");
  const [showResults, setShowResults] = useState(false);

  const handleChange = (value: string) => {
    setInput(value);
    handleInput(value);
  };

  const colors = useContext(ColorContext);
  return (
    <>
      <div className="searchbarContainer" style={{ width: props.width }}>
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
            onFocus={() => setShowResults(true)}
            onBlur={() => setShowResults(false)}
          />
          {/* <label className="searchHotKeyHint">
            {navigator.platform.toUpperCase().indexOf("MAC") >= 0 ? "⌘" : "Ctrl"}+F
          </label> */}
        </div>
        {showResults ? <SearchResults results={props.results} /> : <></>}
      </div>
    </>
  );
}
