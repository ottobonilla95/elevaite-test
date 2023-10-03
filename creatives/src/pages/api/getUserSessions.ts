import { NextApiRequest, NextApiResponse } from "next";
import fs from 'fs';
import path from 'path';

interface UserSession {
  timestamp: number;
  message: string;
  theme: string,
  audience: string,
  gender: string,
  size: string,
  n: string,
  contentType: string,
  color: string,
  folderName: string,
  template: string,
  result: string
}

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  try {
    const {
      timestamp,
      userName,
      llm
    } = req.query;

    /*if (!timestamp || !userName || !llm) {
      return res.status(400).json({ success: false, error: "Missing query parameters" });
    }*/

    
    const userSessionFilePath = path.join(
      process.cwd(),
      'userSessions',
      userName as string,
      llm as string,
      `${userName}.json`
    );

   
    const data = fs.readFileSync(userSessionFilePath, 'utf8');
    const jsonArray: UserSession[] = JSON.parse(data);

    
    const matchingObject = jsonArray.find((obj) => obj.timestamp === parseInt(timestamp as string));

    if (matchingObject) {
      res.status(200).json({ success: true, data: matchingObject });
    } else {
      res.status(200).json({ success: false});
    }
  } catch (error) {
    console.error(error);
    res.status(500).json({ success: false, error: "Error occurred while trying to retrieve user session details" });
  }
}
