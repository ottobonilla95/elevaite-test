/**
 * MFA Configuration utilities for reading environment variables
 * and determining which MFA methods should be available
 */

export interface MFAConfig {
  email: boolean;
  sms: boolean;
  totp: boolean;
  biometric: boolean;
}

/**
 * Parse the NEXT_PUBLIC_MFA_METHODS_ENABLED environment variable and return
 * a configuration object indicating which methods are enabled
 */
export function getMFAConfig(): MFAConfig {
  // Get the environment variable (this will be available at build time)
  const mfaMethodsEnabled =
    process.env.NEXT_PUBLIC_MFA_METHODS_ENABLED || "email";

  // Parse the comma-separated string
  const enabledMethods = mfaMethodsEnabled
    .split(",")
    .map((method) => method.trim().toLowerCase())
    .filter((method) => ["email", "sms", "totp", "biometric"].includes(method));

  // If no valid methods found, fallback to email
  const validMethods = enabledMethods.length > 0 ? enabledMethods : ["email"];

  return {
    email: validMethods.includes("email"),
    sms: validMethods.includes("sms"),
    totp: validMethods.includes("totp"),
    biometric: validMethods.includes("biometric"),
  };
}

/**
 * Check if users are allowed to disable all MFA methods
 */
export function isMFADisableAllowed(): boolean {
  const allowDisableAll =
    process.env.NEXT_PUBLIC_MFA_ALLOW_DISABLE_ALL || "false";
  return allowDisableAll.toLowerCase() === "true";
}

/**
 * Check if at least one MFA method is enabled
 */
export function hasAnyMFAMethodEnabled(): boolean {
  const config = getMFAConfig();
  return config.email || config.sms || config.totp || config.biometric;
}

/**
 * Get the count of enabled MFA methods
 */
export function getEnabledMFAMethodsCount(): number {
  const config = getMFAConfig();
  return [
    config.email,
    config.sms,
    config.totp,
    config.biometric,
  ].filter(Boolean).length;
}

/**
 * Get an array of enabled MFA method names
 */
export function getEnabledMFAMethods(): string[] {
  const config = getMFAConfig();
  const methods: string[] = [];

  if (config.email) methods.push("email");
  if (config.sms) methods.push("sms");
  if (config.totp) methods.push("totp");
  if (config.biometric) methods.push("biometric");

  return methods;
}
