import { LoginPage } from "@repo/ui/pages";
import type { JSX } from "react";

function Login(): JSX.Element {
  return <LoginPage mode={1} signUp={false} />;
}

export default Login;
