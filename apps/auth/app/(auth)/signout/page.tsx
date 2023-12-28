import { logOut } from "../../lib/actions";

async function Signout() {
  await logOut();
  return <></>;
}

export default Signout;
