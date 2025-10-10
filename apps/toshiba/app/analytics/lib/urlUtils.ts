/**
 * URL utility functions for consistent URL construction
 * Handles proper hostname detection and absolute URL building
 */

/**
 * Gets the proper base URL for the application
 * Uses window.location.origin if available, otherwise constructs from protocol and host
 * Fallback to environment variables if needed
 */
export function getBaseUrl(): string {
  // In browser environment
  if (typeof window !== "undefined") {
    // Use the current origin, but validate it's not using system hostname
    const origin = window.location.origin;
    const hostname = window.location.hostname;

    // Check if hostname looks like a system hostname (contains no dots and isn't localhost)
    const isSystemHostname =
      !hostname.includes(".") &&
      hostname !== "localhost" &&
      hostname !== "127.0.0.1";

    if (isSystemHostname) {
      // If we detect a system hostname, try to get the proper URL from environment or use a fallback
      const envUrl =
        process.env.NEXT_PUBLIC_APP_URL ?? process.env.NEXTAUTH_URL;
      if (envUrl) {
        return envUrl;
      }

      // Last resort: use localhost with current port
      const port = window.location.port;
      const protocol = window.location.protocol;
      return `${protocol}//localhost${port ? `:${port}` : ""}`;
    }

    return origin;
  }

  // In server environment, use environment variables
  return (
    process.env.NEXT_PUBLIC_APP_URL ??
    process.env.NEXTAUTH_URL ??
    process.env.NEXTAUTH_URL_INTERNAL ??
    "http://localhost:3000"
  );
}

/**
 * Builds an absolute URL for the given path
 * @param path - The path to append to the base URL (should start with /)
 * @returns Complete absolute URL
 */
export function buildAbsoluteUrl(path: string): string {
  const baseUrl = getBaseUrl();
  // Ensure path starts with /
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  return `${baseUrl}${normalizedPath}`;
}

/**
 * Safely redirects to a path using absolute URL
 * Prevents issues with system hostnames in redirects
 * @param path - The path to redirect to
 */
export function safeRedirect(path: string): void {
  const absoluteUrl = buildAbsoluteUrl(path);
  window.location.replace(absoluteUrl);
}

/**
 * Gets the domain without subdomain from a URL
 * Useful for cookie domain configuration
 */
export function getDomainWithoutSubdomain(url: string | URL): string {
  const urlParts = new URL(url).hostname.split(".");

  return urlParts
    .slice(0)
    .slice(-(urlParts.length === 4 ? 3 : 2))
    .join(".");
}
