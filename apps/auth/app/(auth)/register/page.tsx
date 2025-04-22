import { redirect } from "next/navigation";
import type { JSX } from "react";

export default function Register(): JSX.Element {
  redirect("/login");
}
