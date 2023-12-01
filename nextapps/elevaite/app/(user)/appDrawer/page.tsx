"use client";
import { Card, CardHolder, ColorContext } from "@elevaite/ui";
import { ingestionMethods } from "../../../dummydata";
import "./page.css";
import { useContext } from "react";
import Searchbar from "@elevaite/ui/src/components/search/Searchbar";

export default function Page() {
  const colors = useContext(ColorContext);
  return (
    // <div className="grid sm:max-lg:grid-cols-1 lg:max-2xl:grid-cols-2 2xl:grid-cols-3 3xl:grid-cols-4 gap-4 p-8 w-fit z-10">
    //   {ingestionMethods.map((method) => (
    //     <Card
    //       key={method.iconAlt}
    //       description={method.description}
    //       icon={method.icon}
    //       iconAlt={method.iconAlt}
    //       subtitle={method.subtitle}
    //       title={method.title}
    //       btnLabel="Description"
    //     />
    //   ))}
    // </div>
    <div className="pageContent">
      <header className="welcomeAndSearch">
        <span className="welcome" style={{ color: colors.text }}>
          Welcome to ElevAIte <span style={{ fontWeight: 700 }}>{"Mary"}</span> !
        </span>
        <Searchbar />
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
    </div>
  );
}
