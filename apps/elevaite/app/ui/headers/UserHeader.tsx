"use client";
import { ColorContext } from "@repo/ui/contexts";
import { Searchbar } from "@repo/ui/components";
import { useContext, useState } from "react";
import "./UserHeader.css";
import { userSearchHelper } from "../../lib/searchHelpers";

// interface UserHeaderProps {
//   applications: { title: string; key: string; cards: CardProps[] }[];
// }

function UserHeader(): JSX.Element {
  const colors = useContext(ColorContext);
  const [results, setResults] = useState<
    { key: string; link: string; label: string }[]
  >([]);

  function handleSearchInput(input: string): void {
    "use server";
    const res = userSearchHelper(input);
    setResults(res);
  }

  return (
    <header
      className="welcomeAndSearch"
      style={{
        background: colors.primary as string,
        borderColor: colors.borderColor as string,
      }}
    >
      <span className="welcome" style={{ color: colors.text as string }}>
        Welcome to elevAIte<span style={{ fontWeight: 700 }}> Mary </span>!
      </span>
      <Searchbar
        handleInput={handleSearchInput}
        isJump
        results={results}
        resultsTopOffset="80px"
      />
    </header>
  );
}

export default UserHeader;
