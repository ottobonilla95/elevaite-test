/**
 * Centralized authentication types for consistent error handling across the application.
 */

/**
 * Standard authentication error messages that can be returned by authentication functions.
 * These should be user-friendly messages that can be displayed directly in the UI.
 */
export type AuthErrorMessage =
  | "Invalid credentials."
  | "Account locked. Please try again later or reset your password."
  | "Email not verified."
  | "Too many attempts. Please try again later."
  | "Admin access required."
  | "Something went wrong.";

/**
 * MFA (Multi-Factor Authentication) requirement types.
 * These indicate which type of MFA is required for the user.
 */
export type MfaRequirement =
  | "MFA_REQUIRED_TOTP"
  | "MFA_REQUIRED_SMS"
  | "MFA_REQUIRED_EMAIL"
  | "MFA_REQUIRED_MULTIPLE";

/**
 * MFA error object containing detailed information about the MFA requirement.
 */
export interface MfaError {
  type: "MFA_ERROR";
  error: {
    message: MfaRequirement;
    availableMethods?: string[];
    maskedPhone?: string;
    maskedEmail?: string;
  };
}

/**
 * Complete authentication result type that covers all possible outcomes.
 * - `undefined`: Successful authentication
 * - `AuthErrorMessage`: Authentication failed with a specific error
 * - `MfaRequirement`: MFA is required (simple string format)
 * - `MfaError`: MFA is required (detailed object format)
 */
export type AuthResult =
  | undefined
  | AuthErrorMessage
  | MfaRequirement
  | MfaError;

/**
 * Simplified authentication result for basic login forms that don't handle MFA.
 * This is used by components that only need to handle basic authentication errors.
 */
export type SimpleAuthResult = undefined | AuthErrorMessage;

/**
 * Form data interface for basic email/password authentication.
 */
export interface BasicAuthFormData {
  email: string;
  password: string;
  rememberMe?: boolean;
}

/**
 * Extended form data interface that includes optional MFA code.
 */
export interface ExtendedAuthFormData extends BasicAuthFormData {
  totp_code?: string;
}

/**
 * Authentication function type for basic login (no MFA support).
 */
export type BasicAuthFunction = (
  prevState: string,
  formData: BasicAuthFormData
) => Promise<SimpleAuthResult>;

/**
 * Authentication function type for advanced login (with MFA support).
 */
export type ExtendedAuthFunction = (
  prevState: string,
  formData: ExtendedAuthFormData
) => Promise<AuthResult>;

/**
 * Google authentication function type.
 */
export type GoogleAuthFunction = () => Promise<SimpleAuthResult>;

/**
 * Type guard to check if a result is an MFA error object.
 */
export function isMfaError(result: AuthResult): result is MfaError {
  return (
    typeof result === "object" && result !== null && result.type === "MFA_ERROR"
  );
}

/**
 * Type guard to check if a result is an MFA requirement string.
 */
export function isMfaRequirement(result: AuthResult): result is MfaRequirement {
  return typeof result === "string" && result.startsWith("MFA_REQUIRED_");
}

/**
 * Type guard to check if a result is an authentication error message.
 */
export function isAuthError(result: AuthResult): result is AuthErrorMessage {
  return typeof result === "string" && !result.startsWith("MFA_REQUIRED_");
}

/**
 * Internal error codes used by the backend API.
 * These are mapped to user-friendly messages.
 */
export const AUTH_ERROR_CODES = {
  ACCOUNT_LOCKED: "account_locked",
  RATE_LIMIT_EXCEEDED: "rate_limit_exceeded",
  EMAIL_NOT_VERIFIED: "email_not_verified",
  ADMIN_ACCESS_REQUIRED: "admin_access_required",
  MFA_REQUIRED_TOTP: "MFA_REQUIRED_TOTP",
  MFA_REQUIRED_SMS: "MFA_REQUIRED_SMS",
  MFA_REQUIRED_EMAIL: "MFA_REQUIRED_EMAIL",
  MFA_REQUIRED_MULTIPLE: "MFA_REQUIRED_MULTIPLE",
} as const;

/**
 * Maps internal error codes to user-friendly error messages.
 */
export const ERROR_CODE_TO_MESSAGE: Record<
  string,
  AuthErrorMessage | MfaRequirement
> = {
  [AUTH_ERROR_CODES.ACCOUNT_LOCKED]:
    "Account locked. Please try again later or reset your password.",
  [AUTH_ERROR_CODES.RATE_LIMIT_EXCEEDED]:
    "Too many attempts. Please try again later.",
  [AUTH_ERROR_CODES.EMAIL_NOT_VERIFIED]: "Email not verified.",
  [AUTH_ERROR_CODES.ADMIN_ACCESS_REQUIRED]: "Admin access required.",
  [AUTH_ERROR_CODES.MFA_REQUIRED_TOTP]: "MFA_REQUIRED_TOTP",
  [AUTH_ERROR_CODES.MFA_REQUIRED_SMS]: "MFA_REQUIRED_SMS",
  [AUTH_ERROR_CODES.MFA_REQUIRED_EMAIL]: "MFA_REQUIRED_EMAIL",
  [AUTH_ERROR_CODES.MFA_REQUIRED_MULTIPLE]: "MFA_REQUIRED_MULTIPLE",
};

/**
 * Helper function to map an error code to the appropriate auth result.
 */
export function mapErrorCodeToAuthResult(
  errorCode: string,
  errorData?: any
): AuthResult {
  const mappedResult = ERROR_CODE_TO_MESSAGE[errorCode];

  if (!mappedResult) {
    return "Something went wrong.";
  }

  // Handle MFA requirements with detailed error objects
  if (mappedResult.startsWith("MFA_REQUIRED_")) {
    return {
      type: "MFA_ERROR",
      error: {
        message: mappedResult as MfaRequirement,
        availableMethods: errorData?.availableMethods,
        maskedPhone: errorData?.maskedPhone,
        maskedEmail: errorData?.maskedEmail,
      },
    };
  }

  // Return simple string for regular auth errors
  return mappedResult as AuthErrorMessage;
}

/**
 * Helper function to extract error codes from various error structures.
 */
export function extractErrorCode(error: any): string | null {
  // Check direct message
  if (
    typeof error.message === "string" &&
    ERROR_CODE_TO_MESSAGE[error.message]
  ) {
    return error.message;
  }

  // Check cause.message
  if (
    error.cause &&
    typeof error.cause.message === "string" &&
    ERROR_CODE_TO_MESSAGE[error.cause.message]
  ) {
    return error.cause.message;
  }

  // Check cause.err.message (NextAuth CallbackRouteError structure)
  if (
    error.cause?.err?.message &&
    ERROR_CODE_TO_MESSAGE[error.cause.err.message]
  ) {
    return error.cause.err.message;
  }

  // Check if error message contains any of our error codes
  const errorString = JSON.stringify(error);
  for (const code of Object.values(AUTH_ERROR_CODES)) {
    if (errorString.includes(code)) {
      return code;
    }
  }

  return null;
}

/**
 * Helper function to convert MFA requirement to user-friendly message.
 * This is useful for components that need to display MFA requirements as simple text.
 */
export function mfaRequirementToMessage(requirement: MfaRequirement): string {
  switch (requirement) {
    case "MFA_REQUIRED_TOTP":
      return "Please enter your authenticator code.";
    case "MFA_REQUIRED_SMS":
      return "Please enter the code sent to your phone.";
    case "MFA_REQUIRED_EMAIL":
      return "Please enter the code sent to your email.";
    case "MFA_REQUIRED_MULTIPLE":
      return "Please choose your preferred authentication method.";
    default:
      return "Multi-factor authentication required.";
  }
}
