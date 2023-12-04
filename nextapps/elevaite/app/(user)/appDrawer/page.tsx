"use client";
import { Card, CardHolder, ColorContext, SearchResults, Searchbar } from "@elevaite/ui";
import { ingestionMethods } from "../../../dummydata";
import "./page.css";
import { useContext, useState } from "react";

export default function Page() {
  const colors = useContext(ColorContext);
  const [results, setResults] = useState<{ key: string; link: string; label: string }[]>([]);

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
          Welcome to ElevAIte <span style={{ fontWeight: 700 }}>{"Mary"}</span> !
        </span>
        <Searchbar handleInput={handleSearchInput} results={results} width="280px" />
      </header>
      <div className="cardHolders">
        <CardHolder title="ElevAIte for Support">
          <Card
            key={ingestionMethods[0].iconAlt}
            description={ingestionMethods[0].description}
            icon={ingestionMethods[0].icon}
            iconAlt={ingestionMethods[0].iconAlt}
            subtitle={ingestionMethods[0].subtitle}
            title={ingestionMethods[0].title}
            btnLabel="Description"
          />
          <Card
            key={ingestionMethods[0].iconAlt}
            description={ingestionMethods[0].description}
            icon={ingestionMethods[0].icon}
            iconAlt={ingestionMethods[0].iconAlt}
            subtitle={ingestionMethods[0].subtitle}
            title={ingestionMethods[0].title}
            btnLabel="Description"
          />
        </CardHolder>
        <CardHolder title="ElevAIte for Support">
          <Card
            key={ingestionMethods[0].iconAlt}
            description={ingestionMethods[0].description}
            icon={ingestionMethods[0].icon}
            iconAlt={ingestionMethods[0].iconAlt}
            subtitle={ingestionMethods[0].subtitle}
            title={ingestionMethods[0].title}
            btnLabel="Description"
          />
          <Card
            key={ingestionMethods[0].iconAlt}
            description={ingestionMethods[0].description}
            icon={ingestionMethods[0].icon}
            iconAlt={ingestionMethods[0].iconAlt}
            subtitle={ingestionMethods[0].subtitle}
            title={ingestionMethods[0].title}
            btnLabel="Description"
          />
          <Card
            key={ingestionMethods[0].iconAlt}
            description={ingestionMethods[0].description}
            icon={ingestionMethods[0].icon}
            iconAlt={ingestionMethods[0].iconAlt}
            subtitle={ingestionMethods[0].subtitle}
            title={ingestionMethods[0].title}
            btnLabel="Description"
          />
          <Card
            key={ingestionMethods[0].iconAlt}
            description={ingestionMethods[0].description}
            icon={ingestionMethods[0].icon}
            iconAlt={ingestionMethods[0].iconAlt}
            subtitle={ingestionMethods[0].subtitle}
            title={ingestionMethods[0].title}
            btnLabel="Description"
          />
        </CardHolder>
        <CardHolder title="ElevAIte for Support">
          <Card
            key={ingestionMethods[0].iconAlt}
            description={ingestionMethods[0].description}
            icon={ingestionMethods[0].icon}
            iconAlt={ingestionMethods[0].iconAlt}
            subtitle={ingestionMethods[0].subtitle}
            title={ingestionMethods[0].title}
            btnLabel="Description"
          />
        </CardHolder>
      </div>
    </>
  );
}
