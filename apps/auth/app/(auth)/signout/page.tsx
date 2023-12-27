import { signOut } from "../../../auth";

async function Signout() {
  await signOut({ redirectTo: "/login" });
  return <></>;
}

export default Signout;
