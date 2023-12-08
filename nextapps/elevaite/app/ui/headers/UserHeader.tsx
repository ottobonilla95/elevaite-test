"use client";
import { CardProps, ColorContext, Searchbar } from "@elevaite/ui";
import { useContext, useState } from "react";
import "./UserHeader.css";
import { userSearchHelper } from "../../lib/searchHelpers";

interface UserHeaderProps {
  applications: { title: string; key: string; cards: CardProps[] }[];
}

function UserHeader({ applications, ...props }: UserHeaderProps) {
  const colors = useContext(ColorContext);
  const [results, setResults] = useState<{ key: string; link: string; label: string }[]>([]);

  async function handleSearchInput(input: string) {
    "use server";
    const res = await userSearchHelper(input);
    setResults(res);
  }

  return (
    <header className="welcomeAndSearch" style={{ background: colors.primary, borderColor: colors.borderColor }}>
      <span className="welcome" style={{ color: colors.text }}>
        Welcome to elevAIte<span style={{ fontWeight: 700 }}></span>!
      </span>
      <Searchbar
        handleInput={handleSearchInput}
        results={results}
        width="280px"
        isJump={true}
        resultsTopOffset="80px"
      />
    </header>
  );
}

export default UserHeader;
