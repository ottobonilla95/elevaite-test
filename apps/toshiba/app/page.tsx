import { Card, CardHolder } from "@repo/ui/components";
import Link from "next/link";
import { getApplications } from "../applicationsData";
import "./page.scss";
import { auth } from "../auth";
import { redirect } from "next/navigation";

export default async function Page(): Promise<JSX.Element | never> {
  const session = await auth();


  console.log("=== DEBUG SESSION DATA ===");
  console.log("session?.user:", session?.user);
  console.log("is_manager:", (session?.user as any)?.is_manager);
  console.log("application_admin:", (session?.user as any)?.application_admin);
  console.log("is_superuser:", (session?.user as any)?.is_superuser);

  const isSuperAdmin = (session?.user as any)?.is_superuser === true;
  const isApplicationAdmin = (session?.user as any)?.application_admin === true;
  const isAnyAdmin = isSuperAdmin || isApplicationAdmin;

  const isManager = (session?.user as any)?.is_manager === true;

  if (!isAnyAdmin && !isManager) {
    redirect("/chatbot");
  } else if (isManager && !isAnyAdmin) {
    redirect("/analytics");
  }

  const applications = getApplications(session?.user?.accountMemberships, session);
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
