import { auth } from "./auth";

export const config = {
  // https://nextjs.org/docs/app/building-your-application/routing/middleware#matcher
  matcher: ["/((?!api|_next/static|_next/image|dev-reset|.*\\.png$).*)"],
};

// MFA routes that should be accessible without full authentication
const MFA_ROUTES = ["/mfa", "/mfa-verify"];

export default auth((req) => {
  const { pathname } = req.nextUrl;

  // Allow MFA routes without authentication (user is in the middle of MFA flow)
  if (MFA_ROUTES.some((route) => pathname.startsWith(route))) {
    return;
  }

  // Check if the user needs to reset their password
  if (
    req.auth?.user &&
    "needsPasswordReset" in req.auth.user &&
    req.auth.user.needsPasswordReset === true
  ) {
    // If the user is already on the reset-password page, allow them to proceed
    if (pathname === "/reset-password") {
      return;
    }

    // Otherwise, redirect them to the reset-password page
    const resetPasswordUrl = new URL("/reset-password", req.nextUrl.origin);
    return Response.redirect(resetPasswordUrl);
  }

  // Normal redirect to homepage for authenticated users
  if (req.auth) {
    const ELEVAITE_HOMEPAGE = process.env.ELEVAITE_HOMEPAGE;
    if (!ELEVAITE_HOMEPAGE)
      throw new Error("ELEVAITE_HOMEPAGE does not exist in the env");
    const newUrl = new URL(ELEVAITE_HOMEPAGE, req.nextUrl.origin);
    return Response.redirect(newUrl);
  }
});
