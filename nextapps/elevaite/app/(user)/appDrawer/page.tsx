"use client";
import { Card, CardHolder } from "@elevaite/ui";
import { applications } from "../../../dummydata";
import "./page.css";
import UserHeader from "../../ui/headers/UserHeader";

export default function Page() {
  return (
    <>
      <UserHeader />
      <div className="cardHolders">
        {applications.map((app) => (
          <CardHolder title={app.title} key={app.key}>
            {app.cards.map((card) => (
              <Card key={card.id} {...card} />
            ))}
          </CardHolder>
        ))}
      </div>
    </>
  );
}
