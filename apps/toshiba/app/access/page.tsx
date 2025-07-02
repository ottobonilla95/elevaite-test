import { redirect } from "next/navigation";
import { auth } from "../../auth";
import AccessPageClient from "./AccessPageClient";

export default async function Page(): Promise<JSX.Element | never> {
  const session = await auth();

  const isSuperAdmin = (session?.user as any)?.is_superuser === true;

  if (!isSuperAdmin) {
    redirect("/chatbot");
  }

  return <AccessPageClient />;
}
