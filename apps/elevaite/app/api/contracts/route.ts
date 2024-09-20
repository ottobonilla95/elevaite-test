import { GetObjectCommand, S3Client } from "@aws-sdk/client-s3";
import { Readable } from "node:stream";

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

export async function GET(req, res) {
  const bucketName = "elevaite-contract-assurance";
  const searchParams = req.nextUrl.searchParams;
  const filekey = searchParams.get("key");

  const downloadParams = {
    Key: filekey,
    Bucket: bucketName,
  };

  const { Body } = await s3Client.send(
    new GetObjectCommand({
      Bucket: bucketName,
      Key: filekey,
    })
  );
  //   console.log(Body);

  //   const arrayBuffer = await Body?.transformToWebStream();
  //   const buffer = Buffer.from(arrayBuffer);

  const headers = new Headers();

  headers.set("Content-Type", `application/pdf`);
  headers.set("Content-Disposition", `attachment; filename=${filekey}`);
  //   res
  //     .status(200)
  //     .setHeader("Content-Type", `application/pdf`)
  //     .setHeader("Content-Disposition", `attachment; filename=${filekey}`)
  //     .send(Body?.transformToWebStream());
  //   Readable.from(Body?.transformToByteArray).pipe(res);
  return new Response(Body, { status: 200, statusText: "OK", headers });

  //   res.formData({ file: Body });
}
