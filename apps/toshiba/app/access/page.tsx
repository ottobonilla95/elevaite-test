import { redirect } from "next/navigation";
import { auth } from "../../auth";
import AccessPageClient from "./AccessPageClient";

export default async function Page(): Promise<JSX.Element | never> {
  const session = await auth();

  const isSuperAdmin = (session?.user as any)?.is_superuser === true;
  const isApplicationAdmin = (session?.user as any)?.application_admin === true;
  const isAnyAdmin = isSuperAdmin || isApplicationAdmin;

  if (!isAnyAdmin) {
    redirect("/chatbot");
  }

  return <AccessPageClient isSuperAdmin={isSuperAdmin} />;
}
