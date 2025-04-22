import { Card, CardHolder } from "@repo/ui/components";
import Link from "next/link";
import { getApplications } from "../../../dummydata";
import "./page.scss";
import { auth } from "../../../auth";

export default async function Page(): Promise<JSX.Element> {
  // In development mode, use a mock session
  if (process.env.NODE_ENV === "development") {
    const mockMemberships = [
      {
        account_id: "dev-account-id",
        role_id: "dev-role-id",
        account_name: "Development Account",
      },
    ];
    const applications = getApplications(process.env.NODE_ENV, mockMemberships);
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

  // In production, use real auth
  const session = await auth();
  const applications = getApplications(
    process.env.NODE_ENV,
    session?.user?.accountMemberships
  );

  // function fetchApplications(): { title: string; key: string; cards: CardProps[] }[] {
  //   return getApplications(process.env.NODE_ENV, session?.user.account_memberships);
  // }

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
