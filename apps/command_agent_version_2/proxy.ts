import { auth } from "./auth";

export const proxy = auth;

export const config = {
  // https://nextjs.org/docs/app/building-your-application/routing/proxy#matcher
  matcher: ["/((?!api|_next/static|_next/image|.*\\.png$).*)"],
};
