import { GetObjectCommand, S3Client } from "@aws-sdk/client-s3";
import { type NextRequest } from "next/server";

const region = process.env.AWS_REGION;
const accessKeyId = process.env.AWS_AKID;
const secretAccessKey = process.env.AWS_SAK;

if (!region || !accessKeyId || !secretAccessKey)
  throw new Error("AWS credential or region are not set in env..");

const s3Client = new S3Client({
  region,
  credentials: {
    accessKeyId,
    secretAccessKey,
  },
});

export async function GET(req: NextRequest): Promise<Response> {
  const bucketName = "elevaite-contract-assurance";
  const searchParams = req.nextUrl.searchParams;
  const filekey = searchParams.get("key") ?? "";

  try {
    const { Body } = await s3Client.send(
      new GetObjectCommand({
        Bucket: bucketName,
        Key: filekey,
      })
    );

    if (!Body) {
      return new Response("File not found", { status: 404 });
    }

    const headers = new Headers();
    headers.set("Content-Type", `application/pdf`);
    headers.set("Content-Disposition", `attachment; filename=${filekey}`);
    
    return new Response(Body as ReadableStream, { status: 200, statusText: "OK", headers });
  } catch (error) {
    return new Response("Internal Server Error", { status: 500 });
  }
}
