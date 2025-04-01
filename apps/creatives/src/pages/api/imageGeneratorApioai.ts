import { NextApiRequest, NextApiResponse } from 'next';
import OpenAI from "openai";
import { StringLiteral } from 'typescript';

const openai = new OpenAI();

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
    try {
        
        const prompt = req.query.prompt as string;
        const n = parseInt(req.query.n as string, 10);
        const size = req.query.size as string;
        const response = await openai.images.generate({ prompt: prompt, n:n, size:"1024x1024" });
        //console.log("RESPONSE!!!!:" , response);
        res.status(200).json(response);
    } catch (error) {
        console.error('Error reading images directory:', error);
        res.status(500).json({ error: 'An error occurred' });
    }

}





