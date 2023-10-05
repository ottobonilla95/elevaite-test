import { NextApiRequest, NextApiResponse } from "next";
import fs from 'fs';
import path from 'path';

interface cbList {
  offeringMsg: string;
  cta: string;
  ea: string;
  pFileUrl: string;
  bFileUrl: string;
  urlList: string[];
  userName: string;
}

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  try {
    const { userName } = req.query;

    const FolderPath = path.join(
      process.cwd(),
      'CreativeBriefs',
      userName as string
    );

    try {
        if(fs.existsSync(FolderPath)){
            const filePath = FolderPath + "/cblist.json";
            const data = fs.readFileSync(filePath, 'utf8');
            const jsonArray: cbList[] = JSON.parse(data);
            res.status(200).json({ jsonArray });
        }
      
    } catch (readError) {
      console.error('Error reading file:', readError);
      res.status(500).json({ success: false, error: "Error occurred while trying to read the file" });
    }
    
  } catch (error) {
    console.error(error);
    res.status(500).json({ success: false, error: "Error occurred while trying to retrieve user session details" });
  }
}
