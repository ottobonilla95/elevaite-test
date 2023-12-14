import { AuthError } from "next-auth";
import { signIn } from "@/auth";
import { log } from "console";

export async function authenticate(
  prevState: string | undefined,
  formData: Record<"email" | "password", string>
): Promise<"Invalid credentials." | "Something went wrong." | undefined> {
  "use server";
  try {
    await signIn("credentials", formData);
  } catch (error) {
    log(error);
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
