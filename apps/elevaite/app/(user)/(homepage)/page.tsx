import type { CardProps } from "@repo/ui/components";
import { Card, CardHolder } from "@repo/ui/components";
import Link from "next/link";
import { getApplications } from "../../../dummydata";
import "./page.scss";


export default function Page(): JSX.Element {
  const applications = fetchApplications();

  function fetchApplications(): { title: string; key: string; cards: CardProps[] }[] {
    return getApplications(process.env.NODE_ENV);
  }

  return (
    <div className="card-holders-container">
      {applications.map((app) => (
        <CardHolder key={app.key} title={app.title}>
          {app.cards.map((card) => (
            <Link href={card.link ?? "/"} key={card.id} rel="noopener noreferrer" target={card.openInNewTab ? "_blank" : ""}>
              <Card {...card}/>
            </Link>
          ))}
        </CardHolder>
      ))}
    </div>
  );
}
