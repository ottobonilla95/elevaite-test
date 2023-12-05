"use client";
import { Card, CardHolder, ColorContext, Searchbar } from "@elevaite/ui";
import { applications } from "../../../dummydata";
import "./page.css";
import { useContext, useEffect, useState } from "react";

export default function Page() {
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
    <>
      <header className="welcomeAndSearch" style={{ background: colors.primary }}>
        <span className="welcome" style={{ color: colors.text }}>
          Welcome to elevAIte<span style={{ fontWeight: 700 }}></span>!
        </span>
        <Searchbar handleInput={handleSearchInput} results={results} width="280px" isJump={true} />
      </header>
      <div className="cardHolders">
        <CardHolder title="ElevAIte for Support">
          <Card key={applications.supportBot.iconAlt} {...applications.supportBot} id="supportBot" />
        </CardHolder>
        <CardHolder title="ElevAIte for Finance">
          <Card key={applications.deckBuilder.iconAlt} {...applications.deckBuilder} id="deckBuilder" />
        </CardHolder>
        <CardHolder title="ElevAIte for Revenue">
          <Card key={applications.insights.iconAlt} {...applications.insights} id="insights" />
          <Card key={applications.campaignBuilder.iconAlt} {...applications.campaignBuilder} id="campaignBuilder" />
        </CardHolder>
      </div>
    </>
  );
}
