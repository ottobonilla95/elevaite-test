import { NextApiRequest, NextApiResponse } from 'next';
import axios from 'axios';
import fs from 'fs';
import path from 'path';
import https from 'https';

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
    
    try {

        const folderName = req.query.folerName as string;
        const image = req.query.image as string;
        const prompt = req.query.prompt as string;
        const n = req.query.n as string;
        const size = req.query.size as string;

        const filePath = path.join(process.cwd(), 'public', folderName, image);
        const imageBuffer = fs.readFileSync(filePath);

        const formData = new FormData();
        const blobImage = new Blob([imageBuffer], { type: 'image/png'});


        formData.append('image', blobImage);
        formData.append('prompt', prompt);
        formData.append('n', n);
        formData.append('size', size);

        const axiosInstance = axios.create({
            httpsAgent: new https.Agent({
                rejectUnauthorized: false,
            }),
        });
        
        const response = await axios.post(
            'https://api.openai.com/v1/images/edits',
            formData,
            {
                headers: {
                    Authorization: `Bearer ${process.env.OPENAI_API_KEY}`,
                    'Content-Type': 'multipart/form-data',
                },
            }
        );
        console.log("RESPONSE!!!: ", response.data);
        res.status(200).json(response.data);
        
    } catch (error) {
        console.error('Error making API call:', error);
        res.status(500).json({ error: 'An error occurred while making the API call.' });
    }
}