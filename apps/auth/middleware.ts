import { auth } from "./auth";

export const config = {
  // https://nextjs.org/docs/app/building-your-application/routing/middleware#matcher
  matcher: ["/((?!api|_next/static|_next/image|.*\\.png$).*)"],
};

export default auth((req) => {
  if (req.auth) {
    const ELEVAITE_HOMEPAGE = process.env.ELEVAITE_HOMEPAGE;
    if (!ELEVAITE_HOMEPAGE)
      throw new Error("ELEVAITE_HOMEPAGE does not exist in the env");
    const newUrl = new URL(ELEVAITE_HOMEPAGE, req.nextUrl.origin)
    return Response.redirect(newUrl)
  }
})