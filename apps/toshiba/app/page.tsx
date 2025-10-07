import { Card, CardHolder } from "@repo/ui/components";
import Link from "next/link";
import { getApplications } from "../applicationsData";
import "./page.scss";
import { auth } from "../auth";
import { redirect } from "next/navigation";

export default async function Page(): Promise<JSX.Element | never> {
  const session = await auth();

  const isSuperAdmin = (session?.user as any)?.is_superuser === true;
  const isApplicationAdmin = (session?.user as any)?.application_admin === true;
  const isAnyAdmin = isSuperAdmin || isApplicationAdmin;

  if (!isAnyAdmin) {
    redirect("/chatbot");
  }

  const applications = getApplications(session?.user?.accountMemberships);

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
