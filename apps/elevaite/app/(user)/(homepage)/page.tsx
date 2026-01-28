import { Card, CardHolder } from "@repo/ui/components";
import type { UserAccountMembershipObject } from "@repo/ui/types";
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
        account_name: "Development Account",
        is_admin: false,
        roles: [
          {
            id: "dev-role-id",
            name: "Developer",
          },
        ],
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
    session?.user?.accountMemberships as
      | UserAccountMembershipObject[]
      | undefined,
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
