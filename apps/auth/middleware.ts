import { auth } from "./auth";

export default auth;

export const config = {
  // https://nextjs.org/docs/app/building-your-application/routing/middleware#matcher
  matcher: ["/((?!api|_next/static|_next/image|.*\\.png$).*)"],
};

// ((request) => {
//   if (request.nextUrl.pathname.startsWith("/login/google")) {
//     const requestHeaders = new Headers(request.headers);
//     requestHeaders.set("Referer", "http://localhost:3001/iopex.ai");
//     return NextResponse.redirect(new URL("https://login.iopex.ai/login/google", request.url));
//   }
//   if (request.nextUrl.pathname.startsWith("/iopex.ai")) {
//     console.log(request.headers);
//   }
// });
