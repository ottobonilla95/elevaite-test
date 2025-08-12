"use server";
import { AuthError } from "next-auth";
import { signIn, signOut, auth } from "../../auth";
import {
  type ChatMessageResponse,
  type ChatBotGenAI,
  type ChatbotV,
  type ChatMessageObject,
  type SessionSummaryObject,
  SessionObject,
} from "./interfaces";
import {
  isChatMessageResponse,
  isPastSessionsResponse,
  isSessionSummaryResponse,
} from "./discriminators";
import { headers } from "next/headers";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL;
const FRONTEND_URL =
  process.env.NEXT_PUBLIC_FRONTEND_URL ?? "http://localhost:3002";

export async function authenticate(
  _prevState: string | undefined,
  formData: Record<"email" | "password", string> & { totp_code?: string }
): Promise<
  | "Invalid credentials."
  | "Email not verified."
  | "Account locked. Please try again later or reset your password."
  | "Too many attempts. Please try again later."
  | "Admin access required."
  | "Something went wrong."
  | "MFA_REQUIRED_TOTP"
  | "MFA_REQUIRED_SMS"
  | "MFA_REQUIRED_EMAIL"
  | "MFA_REQUIRED_MULTIPLE"
  | { type: "MFA_ERROR"; error: any }
  | undefined
> {
  try {
    await signIn("credentials", formData);
    return undefined;
  } catch (error) {
    if (error instanceof AuthError) {
      // Helper function to extract custom error message from various NextAuth error structures
      const extractCustomError = (err: any): string | null => {
        // Check direct message
        if (typeof err.message === "string") {
          if (err.message === "account_locked") return "Account locked.";
          if (err.message === "rate_limit_exceeded")
            return "Too many attempts. Please try again later.";
          if (err.message === "email_not_verified")
            return "Email not verified.";
        }

        // Check cause.message
        if (err.cause && typeof err.cause.message === "string") {
          if (err.cause.message === "account_locked") return "Account locked.";
          if (err.cause.message === "rate_limit_exceeded")
            return "Too many attempts. Please try again later.";
          if (err.cause.message === "email_not_verified")
            return "Email not verified.";
        }

        // Check cause.err.message (CallbackRouteError structure)
        if (
          err.cause &&
          err.cause.err &&
          typeof err.cause.err.message === "string"
        ) {
          if (err.cause.err.message === "account_locked")
            return "Account locked.";
          if (err.cause.err.message === "rate_limit_exceeded")
            return "Too many attempts. Please try again later.";
          if (err.cause.err.message === "email_not_verified")
            return "Email not verified.";
        }

        return null;
      };

      // Try to extract custom error message
      const customError = extractCustomError(error);
      if (customError) {
        console.log("DEBUG: Custom error extracted:", customError);
        return customError;
      }

      // Handle CallbackRouteError (NextAuth wrapping our custom errors)
      if (error.type === "CallbackRouteError") {
        // Check for error in cause.err.message (NextAuth structure)
        const causeErr = (error.cause as any)?.err;
        if (causeErr && causeErr.message) {
          if (causeErr.message === "account_locked") {
            return "Account locked.";
          }
          if (causeErr.message === "rate_limit_exceeded") {
            return "Too many attempts. Please try again later.";
          }
          if (causeErr.message === "email_not_verified") {
            return "Email not verified.";
          }
        }
      }

      // Handle CredentialsSignin errors specifically
      if (error.type === "CredentialsSignin") {
        // Check the cause for specific error types
        if (error.cause instanceof Error) {
          if (error.cause.message === "account_locked") {
            return "Account locked.";
          }
          if (error.cause.message === "rate_limit_exceeded") {
            return "Too many attempts. Please try again later.";
          }
          if (error.cause.message === "email_not_verified") {
            return "Email not verified.";
          }
        }
        // If no specific cause, return generic invalid credentials
        return "Invalid credentials.";
      }

      // Check for account locked in the main error message first
      if (error.message?.includes("account_locked")) {
        return "Account locked.";
      }
      // Check for rate limit in the main error message first
      if (error.message?.includes("rate_limit_exceeded")) {
        return "Too many attempts. Please try again later.";
      }

      if (error.cause instanceof Error) {
        // Handle account locked error
        if (error.cause.message === "account_locked") {
          return "Account locked.";
        }
        // Handle rate limit error
        if (error.cause.message === "rate_limit_exceeded") {
          return "Too many attempts. Please try again later.";
        }
        // Handle email not verified error
        if (error.cause.message === "email_not_verified") {
          return "Email not verified.";
        }
        if (error.cause.message === "MFA_REQUIRED_TOTP") {
          return {
            type: "MFA_ERROR",
            error: {
              message: error.cause.message,
              availableMethods: (error.cause as any).availableMethods,
              maskedPhone: (error.cause as any).maskedPhone,
              maskedEmail: (error.cause as any).maskedEmail,
            },
          };
        }
        if (error.cause.message === "MFA_REQUIRED_SMS") {
          return {
            type: "MFA_ERROR",
            error: {
              message: error.cause.message,
              availableMethods: (error.cause as any).availableMethods,
              maskedPhone: (error.cause as any).maskedPhone,
              maskedEmail: (error.cause as any).maskedEmail,
            },
          };
        }
        if (error.cause.message === "MFA_REQUIRED_EMAIL") {
          return {
            type: "MFA_ERROR",
            error: {
              message: error.cause.message,
              availableMethods: (error.cause as any).availableMethods,
              maskedPhone: (error.cause as any).maskedPhone,
              maskedEmail: (error.cause as any).maskedEmail,
            },
          };
        }
        if (error.cause.message === "MFA_REQUIRED_MULTIPLE") {
          return {
            type: "MFA_ERROR",
            error: {
              message: error.cause.message,
              availableMethods: (error.cause as any).availableMethods,
              maskedPhone: (error.cause as any).maskedPhone,
              maskedEmail: (error.cause as any).maskedEmail,
            },
          };
        }
      }

      // Search for our error messages anywhere in the error object
      const errorString = JSON.stringify(error);
      if (errorString.includes("account_locked")) {
        console.log("DEBUG: Found account_locked in error string");
        return "Account locked.";
      }
      if (errorString.includes("rate_limit_exceeded")) {
        console.log("DEBUG: Found rate_limit_exceeded in error string");
        return "Too many attempts. Please try again later.";
      }
      if (errorString.includes("email_not_verified")) {
        console.log("DEBUG: Found email_not_verified in error string");
        return "Email not verified.";
      }

      switch (error.type) {
        case "CredentialsSignin":
          return "Invalid credentials.";
        case "CallbackRouteError":
          if (
            error.cause &&
            typeof error.cause === "object" &&
            "err" in error.cause
          ) {
            const causeError = error.cause.err;
            if (causeError instanceof Error) {
              // Handle our custom authentication errors first
              if (causeError.message === "account_locked") {
                return "Account locked.";
              }
              if (causeError.message === "rate_limit_exceeded") {
                return "Too many attempts. Please try again later.";
              }
              if (causeError.message === "email_not_verified") {
                return "Email not verified.";
              }

              if (causeError.message === "MFA_REQUIRED_TOTP") {
                return {
                  type: "MFA_ERROR",
                  error: {
                    message: causeError.message,
                    availableMethods: (causeError as any).availableMethods,
                    maskedPhone: (causeError as any).maskedPhone,
                    maskedEmail: (causeError as any).maskedEmail,
                  },
                };
              }
              if (causeError.message === "MFA_REQUIRED_SMS") {
                return {
                  type: "MFA_ERROR",
                  error: {
                    message: causeError.message,
                    availableMethods: (causeError as any).availableMethods,
                    maskedPhone: (causeError as any).maskedPhone,
                    maskedEmail: (causeError as any).maskedEmail,
                  },
                };
              }
              if (causeError.message === "MFA_REQUIRED_EMAIL") {
                return {
                  type: "MFA_ERROR",
                  error: {
                    message: causeError.message,
                    availableMethods: (causeError as any).availableMethods,
                    maskedPhone: (causeError as any).maskedPhone,
                    maskedEmail: (causeError as any).maskedEmail,
                  },
                };
              }
              if (causeError.message === "MFA_REQUIRED_MULTIPLE") {
                return {
                  type: "MFA_ERROR",
                  error: {
                    message: causeError.message,
                    availableMethods: (causeError as any).availableMethods,
                    maskedPhone: (causeError as any).maskedPhone,
                    maskedEmail: (causeError as any).maskedEmail,
                  },
                };
              }
            }
          }
          // Check if this is an email verification error
          if (error.message?.includes("email_not_verified")) {
            return "Email not verified.";
          }
          // Check if this is an account locked error
          if (error.message?.includes("account_locked")) {
            return "Account locked.";
          }
          // Check if this is a rate limit error
          if (error.message?.includes("rate_limit_exceeded")) {
            return "Too many attempts. Please try again later.";
          }
          return "Invalid credentials.";
        default:
          // Check if this is an email verification error
          if (error.message?.includes("email_not_verified")) {
            return "Email not verified.";
          }
          // Check if this is an account locked error
          if (error.message?.includes("account_locked")) {
            return "Account locked.";
          }
          // Check if this is a rate limit error
          if (error.message?.includes("rate_limit_exceeded")) {
            return "Too many attempts. Please try again later.";
          }
          // Check if this is an admin access required error
          if (error.message?.includes("admin_access_required")) {
            return "Admin access required.";
          }
          return "Something went wrong.";
      }
    }

    // Check for custom errors
    if (error instanceof Error) {
      if (error.message === "email_not_verified") {
        return "Email not verified.";
      }
      if (error.message === "account_locked") {
        return "Account locked.";
      }
      if (error.message === "rate_limit_exceeded") {
        return "Too many attempts. Please try again later.";
      }
      if (error.message === "MFA_REQUIRED_TOTP") {
        return "MFA_REQUIRED_TOTP";
      }
      if (error.message === "MFA_REQUIRED_SMS") {
        return "MFA_REQUIRED_SMS";
      }
      if (error.message === "MFA_REQUIRED_EMAIL") {
        return "MFA_REQUIRED_EMAIL";
      }
    }

    throw error;
  }
}

export async function logout(): Promise<void> {
  try {
    const session = await auth();
    const accessToken = session?.authToken ?? session?.user?.accessToken;

    if (accessToken) {
      const authApiUrl = process.env.NEXT_PUBLIC_AUTH_API_URL;
      if (authApiUrl) {
        try {
          const apiUrl = authApiUrl.replace("localhost", "127.0.0.1");
          const tenantId = process.env.NEXT_PUBLIC_AUTH_TENANT_ID ?? "default";

          const refreshToken = session?.user?.refreshToken;

          if (refreshToken) {
            await fetch(`${apiUrl}/api/auth/logout`, {
              method: "POST",
              headers: {
                "Content-Type": "application/json",
                Authorization: `Bearer ${accessToken}`,
                "X-Tenant-ID": tenantId,
              },
              body: JSON.stringify({
                refresh_token: refreshToken,
              }),
            });
          }
        } catch (apiError) {
          // Continue with NextAuth signOut even if API call fails
        }
      }
    }
  } catch (error) {
    // Continue with NextAuth signOut even if preparation fails
  }

  await signOut({ redirectTo: "/login" });
}

export async function recoverSession(): Promise<boolean> {
  try {
    const session = await auth();
    const accessToken = session?.authToken ?? session?.user?.accessToken;

    if (!accessToken) {
      return false;
    }

    const authApiUrl = process.env.NEXT_PUBLIC_AUTH_API_URL;
    if (!authApiUrl) {
      return false;
    }

    const apiUrl = authApiUrl.replace("localhost", "127.0.0.1");
    const tenantId = process.env.NEXT_PUBLIC_AUTH_TENANT_ID ?? "default";

    const response = await fetch(`${apiUrl}/api/auth/recover-session`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${accessToken}`,
        "X-Tenant-ID": tenantId,
      },
    });

    if (response.ok) {
      console.log("Session recovery successful");
      return true;
    } else {
      console.error("Session recovery failed:", response.status);
      return false;
    }
  } catch (error) {
    console.error("Error during session recovery:", error);
    return false;
  }
}

export async function fetchChatbotResponse(
  userId: string,
  messageText: string,
  sessionId: string,
  messageHistory: ChatMessageObject[],
  chatbotV: ChatbotV,
  chatbotGenAi: ChatBotGenAI
): Promise<ChatMessageResponse> {
  const url = `${BACKEND_URL ?? ""}run`;
  const response = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      query: messageText,
      uid: userId,
      sid: sessionId,
      messages: messageHistory.slice(-6),
      collection: chatbotGenAi,
    }),
  });
  if (!response.ok) throw new Error("Failed to fetch");
  const data: unknown = await response.json();
  if (isChatMessageResponse(data)) return data;
  throw new Error("Invalid data type");
}

export async function fetchSessionSummary(
  userId: string,
  sessionId: string
): Promise<SessionSummaryObject> {
  const url = new URL(
    `${BACKEND_URL ?? ""}summarization?uid=${userId}&sid=${sessionId}`
  );
  const response = await fetch(url);
  if (!response.ok) throw new Error("Failed to fetch");
  const data: unknown = await response.json();
  if (isSessionSummaryResponse(data)) return data;
  throw new Error("Invalid data type");
}

export async function getImageUrl(
  filename: string
): Promise<string | undefined> {
  "use server";
  const headersList = headers();
  const headerUrl = new URL(FRONTEND_URL);
  console.log("HeaderURL: ", headerUrl);

  try {
    const _url = new URL(`${headerUrl.origin}/api/images`);
    console.log("URL: ", _url);
    _url.searchParams.set("filename", filename);
    console.log("URL: ", _url);
    return _url.toString();
  } catch (error) {
    console.error("Error fetching image:", error);
  }
}

export async function resetPassword(newPassword: string): Promise<{
  success: boolean;
  message: string;
  needsPasswordReset?: boolean;
}> {
  try {
    // Get the auth token from the session
    const session = await auth();

    // Check for access token in different possible locations
    const accessToken =
      session?.authToken ??
      session?.user?.accessToken ??
      (session as { accessToken?: string })?.accessToken;

    if (!accessToken) {
      throw new Error("No auth token found in session");
    }

    const authApiUrl = process.env.NEXT_PUBLIC_AUTH_API_URL;
    if (!authApiUrl) {
      throw new Error(
        "NEXT_PUBLIC_AUTH_API_URL not found in environment variables"
      );
    }

    const tenantId = process.env.NEXT_PUBLIC_AUTH_TENANT_ID ?? "default";

    // Explicitly use IPv4 address instead of localhost to avoid IPv6 issues
    const apiUrl = authApiUrl.replace("localhost", "127.0.0.1");

    // Call the auth-api to change the password
    const response = await fetch(`${apiUrl}/api/auth/change-password`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${accessToken}`,
        "X-Tenant-ID": tenantId,
      },
      body: JSON.stringify({
        new_password: newPassword,
      }),
    });

    if (!response.ok) {
      const errorData: unknown = await response.json();
      console.error("Server Action - Password reset error:", errorData);

      let errorMessage = "Failed to reset password";
      if (
        typeof errorData === "object" &&
        errorData !== null &&
        "detail" in errorData
      ) {
        const detail = (errorData as { detail: unknown }).detail;
        console.log("Server Action - Error detail:", detail, typeof detail);

        if (typeof detail === "string") {
          errorMessage = detail;
        } else if (Array.isArray(detail) && detail.length > 0) {
          // Handle Pydantic validation errors which return an array of error objects
          const firstError = detail[0];
          if (
            typeof firstError === "object" &&
            firstError !== null &&
            "msg" in firstError
          ) {
            errorMessage = String((firstError as { msg: unknown }).msg);
          } else {
            errorMessage = "Password validation failed";
          }
        } else if (detail !== null && detail !== undefined) {
          errorMessage = String(detail);
        }
      }

      console.log(
        "Server Action - Final error message:",
        errorMessage,
        typeof errorMessage
      );
      return {
        success: false,
        message: errorMessage,
      };
    }

    // The auth-api will invalidate all sessions for this user,
    // so the user will need to log in again with their new password
    // Also explicitly return that the user no longer needs to reset their password
    return {
      success: true,
      message: "Password successfully changed",
      needsPasswordReset: false, // Explicitly set to false after successful password reset
    };
  } catch (error) {
    return {
      success: false,
      message:
        error instanceof Error ? error.message : "Failed to reset password",
    };
  }
}

export async function fetchPastSessions(
  userId: string
): Promise<SessionObject[]> {
  const url = new URL(`${BACKEND_URL ?? ""}pastSessions?uid=${userId}`);
  console.log(userId);
  const response = await fetch(url);
  if (!response.ok) throw new Error("Failed to fetch");
  const data: unknown = await response.json();
  console.log("Past Sessions:", data);
  if (isPastSessionsResponse(data)) return data;
  throw new Error("Invalid data type");
}

export async function batchEvaluation(formData: FormData): Promise<any> {
  const url = new URL(`${BACKEND_URL ?? ""}batchEvaluation`);
  const response = await fetch(url, {
    method: "POST",
    // headers: {
    //   "Content-Type": "multipart/form-data",
    // },
    body: formData,
  });
  if (!response.ok) throw new Error("Failed to upload file");
  return await response.json();
}
