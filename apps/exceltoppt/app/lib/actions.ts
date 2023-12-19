"use server";
import { AuthError } from "next-auth";
import { signIn } from "../../auth";

export async function authenticate(
  prevState: string | undefined,
  formData: Record<"email" | "password", string>
): Promise<"Invalid credentials." | "Something went wrong." | undefined> {
  try {
    await signIn("credentials", formData);
  } catch (error) {
    if (error instanceof AuthError) {
      switch (error.type) {
        case "CredentialsSignin":
          return "Invalid credentials.";
        default:
          return "Something went wrong.";
      }
    }
    throw error;
  }
}

export async function uploadToServer(
  formData: FormData
): Promise<{ file_size: string; file_name: string; id: string; sheet_count: string } | undefined> {
  // console.log(formData.get("file"));
  const response = await fetch("http://localhost:8000/upload/", {
    method: "POST",
    body: formData,
  });
  if (!response.ok) throw new Error("Failed to upload");
  // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment -- TODO: Check the validity of the data
  const data = await response.json();
  // eslint-disable-next-line @typescript-eslint/no-unsafe-return -- to be fixed with the above
  return data;
}
