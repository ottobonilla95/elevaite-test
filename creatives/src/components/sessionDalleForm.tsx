import React, { useState, useEffect } from 'react';
import axios from 'axios';
import GeneratedImages2 from '../components/generatedImages2';
import Image from 'next/image';
import { useSession } from 'next-auth/react';
import { time } from 'console';

interface SessionDalleFormProps {
    timestamp: string | null;
    onSessionComplete: (success: boolean) => void;


}
interface ImageData {
    url: string;
}

interface ApiResponse {
    created: number;
    data: ImageData[];
}
const SessionDalleForm: React.FC<SessionDalleFormProps> = ({ timestamp, onSessionComplete }) => {

    console.log(timestamp);
    //console.log(if(timestamp));
    const [userData, setUserData] = useState<any|null>(null);

    const { data: session } = useSession();
    const userName = session?.user?.email?.split("@")[0];


    useEffect(() => {
        if (timestamp === "1695068839795") {
            const fetchUserDate = async () => {
                console.log("inside use effect");
                const response = await axios.get('/api/getUserSessions', {
                    params: {
                        timestamp: timestamp,
                        userName: userName,
                        llm: 'DALLE2',
                    },
                });

                if(response.status === 200){
                    setUserData(response);
                }


            }


        }

    })

    return (
        <div>
            {userData}
        </div>


    );
};

export default SessionDalleForm;
