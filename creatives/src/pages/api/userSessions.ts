import { NextApiRequest, NextApiResponse } from 'next';
import fs from 'fs';
import path from 'path';

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
    try{

       const userName = req.query.userName as string;
       const llm = req.query.llm as string;
        const jsonFilePath = path.join(process.cwd(), 'userSessions', userName, llm, `${userName}.json`);
       

        if(!fs.existsSync(jsonFilePath)){
            res.status(300).json({success:false, filepath: jsonFilePath});
            return;
        }

        const data = fs.readFileSync(jsonFilePath, 'utf-8');
        const userSessionData: { timestamp: number; message: string }[] = JSON.parse(data);
        const result = userSessionData.map(({ timestamp, message }) => ({ timestamp, message }));
        res.status(200).json({success: true,results: result});

    } catch (error) {
        console.log(error);
        res.status(500).json({ error: 'An error occured while processing the request'});
    }
}