"use client";
import { createContext, useContext, useEffect } from "react";



// STRUCTURE 


export interface ChatContextStructure {
   // main interface
}

export const ChatContext = createContext<ChatContextStructure>({
    // Initializers and default data
});



// FUNCTIONS





// PROVIDER

interface ChatContextProviderProps {
    children: React.ReactNode;
}


export function ChatContextProvider(props: ChatContextProviderProps): JSX.Element {

   
  
    return (
        <ChatContext.Provider
            value={ {
                
            } }
        >
            {props.children}
        </ChatContext.Provider>
    );
}
  
export function useChat(): ChatContextStructure {
    return useContext(ChatContext);
}