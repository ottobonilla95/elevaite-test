import type { DBUser } from "./interfaces";
import { isDBUser } from "./interfaces";

const RBAC_BACKEND_URL = process.env.RBAC_BACKEND_URL;
const ORG_ID = process.env.ORG_ID;

export async function registerToBackend({
  firstName,
  lastName,
  email,
  authToken,
}: {
  firstName: string;
  lastName: string;
  email: string;
  authToken: string;
}): Promise<DBUser> {
  if (!RBAC_BACKEND_URL)
    throw new Error("RBAC_BACKEND_URL does not exist in the env");
  const url = new URL(`${RBAC_BACKEND_URL}/register/`);
  const headers = new Headers();
  headers.append("Content-Type", "application/json");
  headers.append("Authorization", `Bearer ${authToken}`);
  const body = JSON.stringify({
    org_id: ORG_ID,
    firstname: firstName,
    lastname: lastName,
    email,
  });
  const res = await fetch(url, {
    body,
    headers,
    method: "POST",
  });
  if (!res.ok) {
    // eslint-disable-next-line no-console -- Need this in case this breaks like that.
    console.error(res.statusText);
    throw new Error("Something went wrong.", { cause: res });
  }
  const data: unknown = await res.json();
  if (isDBUser(data)) return data;
  throw new Error("Malformed Response from server.", { cause: data });
}
