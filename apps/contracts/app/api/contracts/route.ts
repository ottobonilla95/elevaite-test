import { type NextRequest } from "next/server";


export async function GET(req: NextRequest): Promise<Response> {
  const searchParams = req.nextUrl.searchParams;
  const projectId = searchParams.get("projectId") ?? "";
  const contractId = searchParams.get("contractId") ?? "";

  try {
    const CONTRACTS_URL = process.env.NEXT_PUBLIC_CONTRACTS_API_URL;
    const url = new URL(`${CONTRACTS_URL}/projects/${projectId}/files/${contractId}/file`);
    const response = await fetch(url, {method: "GET"});
    const blob = await response.blob();
    const headers = new Headers();
    headers.set("Content-Type", `application/pdf`);
    // headers.set("Content-Disposition", `attachment; filename=${filekey}`);
    
    return new Response(blob , { status: 200, statusText: "OK", headers });
  } catch (error) {
    return new Response("Internal Server Error", { status: 500 });
  }
}
