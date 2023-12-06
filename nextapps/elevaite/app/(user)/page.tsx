import { Card, CardHolder } from "@elevaite/ui";
import { getApplications } from "../../dummydata";
import "./page.css";
import UserHeader from "../ui/headers/UserHeader";

export default async function Page() {
  async function fetchApplications() {
    "use server";
    return getApplications(process.env.NODE_ENV);
  }
  const applications = await fetchApplications();

  return (
    <>
      {/* <UserHeader applications={applications} /> */}
      <div className="cardHolders">
        {applications.map((app) => (
          <CardHolder title={app.title} key={app.key}>
            {app.cards.map((card) => (
              <Card key={card.iconAlt} {...card} />
            ))}
          </CardHolder>
        ))}
      </div>
    </>
  );
}
