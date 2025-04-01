import { NextApiRequest, NextApiResponse } from 'next';
import fs from 'fs';
import path from 'path';

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
    try {
        const {
            userName,
            message,
            llm,
            theme,
            audience,
            gender,
            size,
            n,
            contentType,
            color,
            folderName,
            template,
            result: results, 
        } = req.query;

        const currentTimestamp: number = Date.now();
        

        const userFolderPath = path.join(process.cwd(), 'userSessions', userName as string);

        if (!fs.existsSync(userFolderPath)) {
            fs.mkdirSync(userFolderPath, { recursive: true });
        }

        const llmFolderPath = path.join(process.cwd(), 'userSessions', userName as string, llm as string);

        if (!fs.existsSync(llmFolderPath)) {
            fs.mkdirSync(llmFolderPath, { recursive: true });
        }

        const jsonFilePath = path.join(llmFolderPath, `${userName}.json`);

        let existingContent: any[] = [];
        if(fs.existsSync(jsonFilePath)) {
            const fileContent = fs.readFileSync(jsonFilePath, 'utf-8');
            existingContent = JSON.parse(fileContent);
        }

        const newData = {
            timestamp: currentTimestamp,
            message: message as string,
            theme: theme as string,
            audience: audience as string,
            gender: gender as string,
            size: size as string,
            n: n as string,
            contentType: contentType as string,
            color: color as string,
            folderName: folderName as string,
            template: template as string,
            result: results //Array.isArray(results) ? results : [results], // Ensure "result" is an array
        };
        existingContent.push(newData);

        /*if (!fs.existsSync(jsonFilePath)) {
            fs.writeFileSync(jsonFilePath, JSON.stringify(existingContent));
        } else {
            fs.appendFileSync(jsonFilePath, JSON.stringify(existingContent));
        }*/

        fs.writeFileSync(jsonFilePath, JSON.stringify(existingContent, null, 2));

        // Send a success response with the result
        res.status(200).json({ success: true });
    } catch (error) {
        console.error(error);
        res.status(500).json({ error: 'An error occurred while making the API call' });
    }
}
