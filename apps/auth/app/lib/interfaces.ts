export interface DBUser {
  id: string;
  organization_id: string;
  firstname: string;
  lastname: string;
  email: string;
  is_superadmin: boolean;
  created_at: string;
  updated_at: string;
}

function isObject(item: unknown): item is object {
  return Boolean(item) && item !== null && typeof item === "object";
}

export function isDBUser(obj: unknown): obj is DBUser {
  return isObject(obj) && "is_superadmin" in obj && "organization_id" in obj;
}
