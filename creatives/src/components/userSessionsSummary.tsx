import { useState, useEffect } from 'react';
import { MdChatBubble } from 'react-icons/md';

interface UserSessionsSummaryProps {
  userName: string | undefined;
  llm: string;
  refresh: boolean;
  onSessionSelect: (timestamp: number) => void;
}

interface Session {
  timestamp: number;
  message: string;
}

function truncateText(text: string): string {
  const words = text.split(' ');
  if (words.length > 6) {
    return words.slice(0, 4).join(' ') + '...';
  }
  return text;
}

function UserSessionsSummary({ userName, llm, refresh, onSessionSelect }: UserSessionsSummaryProps) {
  const [sessionData, setSessionData] = useState<Session[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch(`/api/userSessions?userName=${userName}&llm=${llm}`);
        if (!response.ok) {
          throw new Error('Failed to fetch data');
        }
        const data = await response.json();
        console.log("result from api: " + response)
        setSessionData(data.results);
        setLoading(false);
        
      } catch (error) {
        
        setLoading(false);
        
      }
    };
    fetchData();
    if(refresh){
      fetchData();
    }
    
  }, [userName, llm, refresh]);

  if (error) {
    return <p>Error: {error.message}</p>;
  }

 
  const reversedSessionData = [...sessionData].reverse();

  return (
    <div>
      <div className="banner-header">
        <p> User Sessions Summary </p>
      </div>
      <ul className="session-list">
        {reversedSessionData.map((session, index) => (
          <li key={index}>
            <a
              href="#"
              className="session-row"
              onClick={() => onSessionSelect(session.timestamp)} 
            >
              <div style={{ display: 'flex', alignItems: 'center' }}>
                <MdChatBubble style={{ marginRight: '5px' }} />{' '}
                <p style={{ margin: '0 5px' }}>{truncateText(session.message)}</p>
              </div>
            </a>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default UserSessionsSummary;
