import { NextApiRequest, NextApiResponse } from "next";
import fs from 'fs';
import path from 'path';

interface UserData {
    username: string,
    password: string
}

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
    try{

        const {
            userName,
            password
        } = req.query;
        
        //Use details stored in - custom-authentication.json
        const customAuthFile = path.join(process.cwd(), 'src', 'config', 'custom-authentication.json');

        if(!fs.existsSync(customAuthFile)){
            res.status(404).json({success: false, error: "custom authentication file does not exist - please contact admin"})
        }

        const userData = fs.readFileSync(customAuthFile, 'utf8');
        const jsonArray: UserData[] = JSON.parse(userData);

        const userFound = jsonArray.find((obj) => obj.username === userName as string && obj.password === password as string);

        if(userFound){
            res.status(200).json({sucess:true});
        } else {
            res.status(404).json({success:false, error: "user not found"});
        }

    } catch(error){
        console.error(error);
        res.status(500).json({ success: false, error: "Error occurred while trying to retrieve user details" });

    }
}