"use client";

/**
 * Client-side logout helper that clears client storage and then calls the
 * server-side logout endpoint to clear cookies and redirect to /login.
 */
export async function clientLogout(): Promise<void> {
  try {
    if (typeof window !== "undefined") {
      // Clear any per-session data that might depend on the user
      try {
        sessionStorage.clear();
      } catch {}
      // If you later add localStorage-based user state, clear specific keys here
      // e.g., localStorage.removeItem("some-user-key");
    }
  } finally {
    // Use the API route so the server returns the redirect response and clears cookies
    if (typeof window !== "undefined") {
      window.location.href = "/api/logout";
    }
  }
}

