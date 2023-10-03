import { NextApiHandler, NextApiRequest } from "next";
import formidable from "formidable";
import path from "path";
import fs from "fs/promises";

export const config = {
  api: {
    bodyParser: false,
  },
};

const readFile = (
  req: NextApiRequest,
  saveLocally?: boolean
): Promise<{ fields: formidable.Fields; files: formidable.Files }> => {
  const options: formidable.Options = {};
  if (saveLocally) {
    const fileLocation  = req.query.fileLocation as string;
    options.uploadDir = path.join(process.cwd(), 'public',fileLocation);
    options.filename = (name, ext, path, form) => {
      return Date.now().toString() + "_" + path.originalFilename;
    };
  }
  options.maxFileSize = 4000 * 1024 * 1024;
  const form = formidable(options);
  return new Promise((resolve, reject) => {
    form.parse(req, (err, fields, files) => {
      if (err) reject(err);
      resolve({ fields, files });
    });
  });
};

const handler: NextApiHandler = async (req, res) => {
  try {
    const fileLocation  = req.query.fileLocation as string;
    await fs.readdir(path.join(process.cwd(), 'public',fileLocation));
  } catch (error) {
    const fileLocation  = req.query.fileLocation as string;
    await fs.mkdir(path.join(process.cwd(), 'public',fileLocation));
  }
  await readFile(req, true);
  res.json({ done: "ok" });
};

export default handler;