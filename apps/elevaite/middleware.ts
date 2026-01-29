import { auth } from "./auth";

// Middleware that checks authentication for all environments
export default auth((req) => {
  if (req.auth?.user.accountMemberships) {
    const newUrl = new URL("/", req.nextUrl.origin);
    const isAlcatel =
      req.auth.user.accountMemberships.filter(
        (membership) =>
          membership.account_id === "ab5eed01-46f1-423d-9da0-093814a898fc",
      ).length > 0;
    if (req.nextUrl.pathname !== "/" && isAlcatel)
      return Response.redirect(newUrl);
  }
  const LOGIN_URL = process.env.NEXTAUTH_URL;
  if (!LOGIN_URL) throw new Error("NEXTAUTH_URL not found in env");
  if (!req.auth) {
    return Response.redirect(LOGIN_URL);
  }
});

export const config = {
  // https://nextjs.org/docs/app/building-your-application/routing/middleware#matcher
  matcher: ["/((?!api|_next/static|_next/image|.*\\.png$).*)"],
};
