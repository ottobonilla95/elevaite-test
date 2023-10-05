import { NextApiRequest, NextApiResponse } from 'next';
import fs from 'fs';
import path from 'path';

function generateUniqueID(): string {
    const timestamp: number = Date.now();
    const randomPart: string = Math.floor(Math.random() * 10000).toString().padStart(4, '0');
    const uniqueId: string = timestamp.toString().substr(-4) + randomPart;
    return uniqueId;
}

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
    try {
        const {
            targetAudience,
            gender,
            seasonal,
            regional,
            occasion,
            creativeDescription,
            contentType,
            color,
            size,
            imageCount,
            urlList,
            offeringMsg,
            cta,
            ea,
            pFileUrl,
            bFileUrl,
            selectedUrlList,
            userName
        } = req.query;


        const urlListArray = urlList ? (typeof urlList === 'string' ? urlList.split(',') : []) : ([]);


        const selectedUrlListArray = selectedUrlList ? (typeof selectedUrlList === 'string' ? selectedUrlList.split(',') : []) : ([]);

        const ID = generateUniqueID();

        const CBFolderPath = path.join(process.cwd(), 'CreativeBriefs', userName as string);

        if (!fs.existsSync(CBFolderPath)) {
            fs.mkdirSync(CBFolderPath, { recursive: true });
        }

        const jsonFilePath = path.join(CBFolderPath, `cblist.json`);

        let existingContent: any[] = [];
        if (fs.existsSync(jsonFilePath)) {
            const fileContent = fs.readFileSync(jsonFilePath, 'utf-8');
            existingContent = JSON.parse(fileContent);
        }

        const newData = {
            ID: ID,
            targetAudience: targetAudience as string,
            gender: gender as string,
            seasonal: seasonal as string,
            regional: regional as string,
            occasion: occasion as string,
            creativeDescription: creativeDescription as string,
            contentType: contentType as string,
            color: color as string,
            size: size as string,
            imageCount: imageCount as string,
            urlList: urlListArray,
            offeringMsg: offeringMsg as string,
            cta: cta as string,
            ea: ea as string,
            pFileUrl: pFileUrl as string,
            bFileUrl: bFileUrl as string,
            selectedUrlList: selectedUrlListArray,
            userName: userName as string

        };
        existingContent.push(newData);

        fs.writeFileSync(jsonFilePath, JSON.stringify(existingContent, null, 2));

        // Send a success response with the result
        res.status(200).json({ success: true , ID: ID});
    } catch (error) {
        console.error(error);
        res.status(500).json({ error: error });
    }
}
