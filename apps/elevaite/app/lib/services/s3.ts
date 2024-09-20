import type { Readable } from "node:stream";
import { S3Client, GetObjectCommand } from "@aws-sdk/client-s3";

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

function parseS3Url(url: string): { bucketName: string; key: string } {
  try {
    const parsedUrl = new URL(url);

    const bucketName = parsedUrl.hostname.split(".")[0];

    const key = parsedUrl.pathname.slice(1).replace(/%20/g, " "); // Remove leading slash and replace blanks

    if (!bucketName || !key) {
      throw new Error("Invalid S3 URL format.");
    }

    return { bucketName, key };
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : String(error);
    throw new Error(`Failed to parse S3 URL: ${errorMessage}`);
  }
}

function streamToBuffer(stream: Readable): Promise<Buffer> {
  const chunks: Buffer[] = [];
  return new Promise((resolve, reject) => {
    stream.on("data", (chunk: Buffer) => chunks.push(chunk));
    stream.on("end", () => {
      resolve(Buffer.concat(chunks));
    });
    stream.on("error", reject);
  });
}

export async function getFileFromS3(url: string): Promise<Buffer> {
  const { bucketName, key } = parseS3Url(url);

  const { Body } = await s3Client.send(
    new GetObjectCommand({
      Bucket: bucketName,
      Key: key,
    })
  );

  return streamToBuffer(Body as Readable);
}
