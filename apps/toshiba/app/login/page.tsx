import { LoginForm } from "../components/LoginForm";
import { auth } from "../../auth";
import { redirect } from "next/navigation";

export default async function LoginPage() {
  const session = await auth();
  
  // If the user is already logged in, redirect to the home page
  if (session?.user) {
    redirect("/");
  }
  
  return <LoginForm />;
}
