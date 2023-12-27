"use server";
export async function googleLogin(referer: string): Promise<void> {
  const res = await fetch("https://login.iopex.ai/login/google", {
    method: "GET",
    redirect: "follow",
    headers: { Referer: referer },
  });
  console.log(res.ok);
  const data = await res.text();
  console.log(data);
}
