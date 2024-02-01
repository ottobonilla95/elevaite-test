"use client";
import { useContext, useEffect, useRef, useState } from "react";
import { ColorContext } from "../../contexts";
import SVGMagnifyingGlass from "../icons/elevaite/svgMagnifyingGlass";
import { SearchResults } from "./SearchResults";
import "./Searchbar.scss";



const SEARCH_KEY = "K";



interface SearchBarProps {
  handleInput: (term: string) => void;
  results: { key: string; link: string; label: string }[];
  resultsTopOffset: string;
  isJump?: boolean;
}

export function Searchbar({ handleInput, ...props }: SearchBarProps): JSX.Element {
  const [showResults, setShowResults] = useState(false);
  const inputRef = useRef<HTMLInputElement|null>(null);
  const colors = useContext(ColorContext);


  useEffect(() => {
    window.addEventListener("keydown", (e) => {
      if (e.repeat) return;
      if ((e.ctrlKey || e.metaKey) && e.code === `Key${SEARCH_KEY}`) {        
        e.preventDefault();
        if (inputRef.current) inputRef.current.focus();
      }      
    })
  }, []);


  function handleChange (value: string): void {
    handleInput(value);
  };

  function handleResultClick (targetId?: string): void {
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


  function getHotkeyHint(): string {
    if (!global.navigator.platform) return "";
    if (global.navigator.platform.toUpperCase().includes("MAC") || global.navigator.platform === "iPhone") return `⌘+${SEARCH_KEY}`;
    return `Ctrl+${SEARCH_KEY}`;
  }


  return (
    <div className="searchbar-container"
      onBlur={() =>
        setTimeout(() => {
          setShowResults(false);
        }, 100)
      }
      onFocus={() => {
        setShowResults(true);
      }}
    >
      <div className="searchbar">
        <SVGMagnifyingGlass />
        <input
          onChange={(e) => { handleChange(e.target.value); }}
          placeholder="Find answers"
          ref={inputRef}
          style={{ background: colors.background, color: colors.text }}
          type="search"
        />
        <span className="hotkey-hint">
          {getHotkeyHint()}
        </span>
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
