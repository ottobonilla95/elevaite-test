import fs from 'fs';
import path from 'path';
import { NextApiRequest, NextApiResponse } from 'next';

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
    const { id, offeringMsg, cta, ea, pFileUrl, bFileUrl, selectedUrlList, userName } = req.query;

    // Read the JSON file
    const filePath = path.join(process.cwd(), 'CreativeBriefs', userName as string, 'cblist.json');
    const jsonData = JSON.parse(fs.readFileSync(filePath, 'utf8'));

    // Find the object based on ID
    const updatedData = jsonData.map((item: { ID: string; }) => {
        if (item.ID === id) {
            return {
                ...item,
                offeringMsg,
                cta,
                ea,
                pFileUrl,
                bFileUrl,
                selectedUrlList,
            };
        }
        return item;
    });

    // Write the updated data back to the JSON file
    fs.writeFileSync(filePath, JSON.stringify(updatedData, null, 2));

    // Find and return the updated object
    const updatedObject = updatedData.find((item: { ID: string | string[] | undefined; }) => item.ID === id);

    if (!updatedObject) {
        res.status(404).json({ message: 'Object with specified ID not found' });
    } else {
        res.status(200).json({});
    }
};
