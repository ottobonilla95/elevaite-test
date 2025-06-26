import { type NextRequest, NextResponse } from "next/server";
import { GetObjectCommand, S3Client } from "@aws-sdk/client-s3";
import { getSignedUrl } from "@aws-sdk/s3-request-presigner";

// Force dynamic rendering
export const dynamic = "force-dynamic";

// Initialize S3 client lazily to avoid build-time errors
let s3Client: S3Client | null = null;

function getS3Client(): S3Client {
  if (!s3Client) {
    const AWS_AKID = process.env.AWS_AKID;
    if (!AWS_AKID)
      throw new Error("AWS Access Key ID is not present in the environment");

    const AWS_SAK = process.env.AWS_SAK;
    if (!AWS_SAK)
      throw new Error(
        "AWS Secret Access Key is not present in the environment"
      );

    s3Client = new S3Client({
      credentials: {
        accessKeyId: AWS_AKID,
        secretAccessKey: AWS_SAK,
      },
      region: process.env.AWS_REGION,
    });
  }
  return s3Client;
}

export async function GET(req: NextRequest): Promise<NextResponse> {
  try {
    const AWS_BUCKET_NAME = process.env.AWS_BUCKET_NAME;
    if (!AWS_BUCKET_NAME) {
      throw new Error("AWS Bucket Name is not present in the environment");
    }

    const searchParams = req.nextUrl.searchParams;
    const filename = searchParams.get("filename") ?? "";
    const command = new GetObjectCommand({
      Bucket: AWS_BUCKET_NAME,
      // Key: `toshiba_pdf_img/${filename}`,
      Key: `toshiba_6800_6200/${filename}`,
    });

    const s3 = getS3Client();
    const url = await getSignedUrl(s3, command);
    const response = await fetch(url, { method: "GET" });
    const blob = await response.blob();
    const headers = new Headers();
    headers.set(
      "Content-Type",
      response.headers.get("Content-Type") ?? "image/png"
    );

    return new NextResponse(blob, { status: 200, statusText: "OK", headers });
    // return new Response(blob, { status: 200, statusText: "OK", headers });
  } catch (error) {
    console.error("Error fetching image from S3:", error);
    return new NextResponse("Error fetching image from S3");
  }
}
