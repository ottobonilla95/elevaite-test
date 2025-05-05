import { Card, CardHolder } from "@repo/ui/components";
import Link from "next/link";
import { getApplications } from "../../applicationsData";
import "./page.scss";
import { auth } from "../../auth";

export default async function Page(): Promise<JSX.Element> {
  const session = await auth();
  const applications = getApplications(
    process.env.NODE_ENV,
    session?.user?.accountMemberships
  );

  return (
    <div className="card-holders-container">
      {applications.map((app) => (
        <CardHolder key={app.key} title={app.title}>
          {app.cards.map((card) => (
            <Link
              href={card.link ?? "/"}
              key={card.id}
              rel="noopener noreferrer"
              target={card.openInNewTab ? "_blank" : ""}
            >
              <Card {...card} />
            </Link>
          ))}
        </CardHolder>
      ))}
    </div>
  );
}
