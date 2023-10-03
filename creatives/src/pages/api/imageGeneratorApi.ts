import { NextApiRequest, NextApiResponse } from 'next';
import axios from 'axios';
import https from 'https';

export default async function handler(req: NextApiRequest, res: NextApiResponse) {

    try{
        const prompt = req.query.prompt as string;
        const n = req.query.n as string;
        const size = req.query.size as string;

        const formData = new FormData();

        formData.append('prompt', prompt);
        formData.append('n',n);
        formData.append('size', size);

        const response = await axios.post(
            'https://api.openai.com/v1/images/generations',
            {
                prompt: prompt,
                n: n,
                size: size
            },
            {
                headers: {
                    Authorization: `Bearer ${process.env.OPENAI_API_KEY}`,
                    'Content-Type': 'multipart/form-data',
                },
            }
        );
        res.status(200).json(response.data);
    } catch (error) {
        console.error('Error making API call: ', error);
        res.status(500).json({error: 'An error occured while making the API call.'});
    }
}