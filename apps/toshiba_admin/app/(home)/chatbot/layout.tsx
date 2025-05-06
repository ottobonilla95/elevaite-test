import { ChatContextProvider } from "../../ui/contexts/ChatContext";

// eslint-disable-next-line @typescript-eslint/require-await -- pretty sure this has to be async
export default async function RootLayout({ children, }: Readonly<{ children: React.ReactNode; }>): Promise<JSX.Element> {

    return (
        <ChatContextProvider>
            {children}
        </ChatContextProvider>
    );
}