import React, { useState } from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faPaperPlane } from '@fortawesome/free-solid-svg-icons';
import axios from 'axios';
import LinearIndeterminate from './linearIntermediate';

interface Message {
    text: string;
    isUser: boolean;
}

interface ChatWindowProps {
    workbook_name: string | string[] | undefined
    sheet_name: string | string[] | undefined;
}
const ChatWindow: React.FC<ChatWindowProps> = ({ workbook_name, sheet_name }) => {
    console.log("workook_name: ", workbook_name, "sheet_name: ", sheet_name);
    const [messages, setMessages] = useState<Message[]>([]);
    const [newMessage, setNewMessage] = useState('');
    const [isLoading, setIsLoading] = useState(false);

    const handleKeyDown = (e: any) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }
    };

    const handleSendMessage = async () => {
        if (newMessage.trim() === '') return;

        const newUserMessage: Message = { text: newMessage, isUser: true };
        setMessages([...messages, newUserMessage]);
        setNewMessage('');

        const validExcelFile = workbook_name ? (Array.isArray(workbook_name) ? workbook_name[0] : workbook_name) : '';
        const validSheetName = sheet_name ? (Array.isArray(sheet_name) ? sheet_name[0] : sheet_name) : '';
        const q_params = "workbook_name=" + encodeURIComponent(validExcelFile) + "&sheet_name=" + encodeURIComponent(validSheetName) + "&question=" + encodeURIComponent(newMessage);
        console.log("calling api..");
        setIsLoading(true);
        const response = await axios.get(`http://localhost:8000/askagent/?${q_params}`);
        console.log(response);

        if (response.status === 200) {
            setIsLoading(false);
            const botResponse: Message = { text: response.data, isUser: false };
            setMessages((prevMessages) => [...prevMessages, botResponse]);
        }

    };

    return (


        <div className="chatwindow">
            <div className="chat-header-frame">
                <div className="frame-wrapper">
                    <div className="div-wrapper">
                        <div className="text-wrapper">ChatBot</div>
                    </div>
                </div>
            </div>
            <div className="message-container">
                {messages.slice(0).reverse().map((message, index) => (
                    <div
                        key={index}
                        className="message"
                        style={{
                            textAlign: message.isUser ? 'left' : 'right',
                            marginTop: '10px',
                            marginBottom: '10px',
                            height: '35px',
                        }}
                    >
                        <div
              className="user-icon"
              style={{
                marginRight: message.isUser ? '10px' : '0', // Add marginRight only for user messages
                marginLeft: message.isUser ? '0' : '10px', // Add marginLeft only for bot messages
              }}
            >
              {message.isUser ? <img className="chat-avatar" alt="Avatars" src="/img/avatars.png" /> : <img className="bot-avatar" alt="Avatars" src="/img/avatar-4.png" />}
            </div>
                        <div
                            style={{
                                display: 'inline-block',
                                backgroundColor: 'white',
                                color: 'black',
                                borderRadius: '10px',
                                padding: '5px',
                                fontSize: '12px',
                                border: '1px solid #E7E7E7'
                            }}
                        >
                            {message.text}
                        </div>
                    </div>
                ))}
            </div>
            {isLoading ? (<div className="dot-pulse-container">
                <div className="dot-pulse"></div>
            </div>) : ("")}


            <div className="chattextbox">
                <div className="chatgroup">
                    <img className="user-avatar" alt="Avatars" src="/img/avatars.png" />
                    <input
                        type="text"
                        value={newMessage}
                        onChange={(e) => setNewMessage(e.target.value)}
                        placeholder="Type a message..."
                        onKeyDown={handleKeyDown}
                        className="comment-input" />
                </div>
                <div className="send-box">
                    <FontAwesomeIcon icon={faPaperPlane} onClick={handleSendMessage} style={{ cursor: "pointer" }} />
                </div>
            </div>



        </div>



    );
};

export default ChatWindow;
