"use client";
import { ColorContext, Searchbar } from "@elevaite/ui";
import { useContext, useEffect, useState } from "react";

function UserHeader() {
  const colors = useContext(ColorContext);
  const [results, setResults] = useState<{ key: string; link: string; label: string }[]>([]);

  useEffect(() => {
    handleSearchInput("");
  }, []);

  function handleSearchInput(term: string) {
    const promise: Promise<{ key: string; link: string; label: string }[]> = new Promise((resolve, reject) => {
      const refs: { key: string; link: string; label: string }[] = [
        { key: "supportBot", label: "Support Bot", link: "#supportBot" },
        { key: "deckBuilder", label: "AI Deck Builder", link: "#deckBuilder" },
        { key: "insights", label: "Insights", link: "#insights" },
        { key: "campaignBuilder", label: "Campaign Builder", link: "#campaignBuilder" },
      ];
      resolve(refs.filter((ref) => ref.label.toLowerCase().includes(term.toLowerCase())));
    });
    promise.then((res) => setResults(res));
  }
  return (
    <header className="welcomeAndSearch" style={{ background: colors.primary, borderColor: colors.borderColor }}>
      <span className="welcome" style={{ color: colors.text }}>
        Welcome to elevAIte<span style={{ fontWeight: 700 }}></span>!
      </span>
      <Searchbar handleInput={handleSearchInput} results={results} width="280px" isJump={true} />
    </header>
  );
}

export default UserHeader;
