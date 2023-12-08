import type { CardProps } from "@repo/ui/components";
import { Card, CardHolder } from "@repo/ui/components";
import { getApplications } from "../../dummydata";
import "./page.css";

export default function Page(): JSX.Element {
  function fetchApplications(): { title: string; key: string; cards: CardProps[] }[] {
    return getApplications(process.env.NODE_ENV);
  }
  const applications = fetchApplications();

  return (
    <>
      {/* <UserHeader applications={applications} /> */}
      <div className="cardHolders">
        {applications.map((app) => (
          <CardHolder key={app.key} title={app.title}>
            {app.cards.map((card) => (
              <a href={card.link} key={card.id} rel="noopener noreferrer" target="_blank">
                <Card {...card} />
              </a>
            ))}
          </CardHolder>
        ))}
      </div>
    </>
  );
}
