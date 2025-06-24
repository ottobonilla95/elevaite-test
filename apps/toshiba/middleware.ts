import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";
import { auth } from "./auth";

export async function middleware(request: NextRequest): Promise<NextResponse> {
  const session = await auth();
  const requestHeaders = new Headers(request.headers);
  console.log("Middleware - Request URL:", request.url);
  requestHeaders.set("x-url", request.url);

  // Allow access to login and forgot-password pages without a session
  if (
    request.nextUrl.pathname === "/login" ||
    request.nextUrl.pathname === "/forgot-password"
  ) {
    return NextResponse.next();
  }

  // If user is not logged in, redirect to login
  if (!session?.user) {
    return NextResponse.redirect(new URL("/login", request.url));
  }

  const needsPasswordReset = session.user.needsPasswordReset === true;

  if (request.nextUrl.pathname === "/reset-password") {
    try {
      const authApiUrl = process.env.AUTH_API_URL;
      if (authApiUrl && session.authToken) {
        const tenantId = process.env.AUTH_TENANT_ID ?? "default";

        const response = await fetch(`${authApiUrl}/api/auth/me`, {
          method: "GET",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${session.authToken}`,
            "X-Tenant-ID": tenantId,
          },
        });

        if (response.ok) {
          const userData = (await response.json()) as {
            is_password_temporary?: boolean;
          };
          const actualNeedsReset = userData.is_password_temporary === true;

          if (!actualNeedsReset && needsPasswordReset) {
            try {
              const baseUrl = request.nextUrl.origin;
              const updateResponse = await fetch(
                `${baseUrl}/api/auth/update-session`,
                {
                  method: "POST",
                  headers: {
                    "Content-Type": "application/json",
                    Cookie: request.headers.get("cookie") ?? "",
                  },
                  body: JSON.stringify({ needsPasswordReset: false }),
                }
              );

              if (updateResponse.ok) {
                console.log(
                  "Middleware - Updated session needsPasswordReset to false"
                );
                return NextResponse.redirect(new URL("/", request.url));
              } else {
                console.error("Middleware - Failed to update session");
              }
            } catch (updateError) {
              console.error(
                "Middleware - Error updating session:",
                updateError
              );
            }
          }

          if (actualNeedsReset) {
            return NextResponse.next();
          }

          return NextResponse.redirect(new URL("/", request.url));
        }
      }
    } catch (error) {
      console.error("Middleware - Error checking password status:", error);
    }

    return NextResponse.next();
  }

  if (needsPasswordReset) {
    return NextResponse.redirect(new URL("/reset-password", request.url));
  }

  return NextResponse.next({
    request: {
      // Apply new request headers
      headers: requestHeaders,
    },
  });
}

export const config = {
  // Include all paths except static assets, API routes, forgot-password, and login pages
  matcher: [
    "/((?!api|_next/static|_next/image|favicon.ico|forgot-password|login).*)",
  ],
};
