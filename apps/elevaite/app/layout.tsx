import { ColorContextProvider } from "@repo/ui/contexts";
import { SessionProvider } from "next-auth/react";
import { Inter } from "next/font/google";
import { auth } from "../auth";
import "./layout.scss";
import { EngineerTheme } from "./ui/themes";
import { RolesContextProvider } from "./lib/contexts/RolesContext";


const font = Inter({ subsets: ["latin"] });


interface RootLayoutProps {
    children: React.ReactNode
}

export default async function RootLayout({children}: RootLayoutProps): Promise<JSX.Element> {


    const session = await auth();
    if (session?.user) {
        // filter out sensitive data before passing to client.
        session.user = {
            id: session.user.id,
            name: session.user.name,
            email: session.user.email,
            image: session.user.image,
        };
    }


    return (
        <html lang="en">
            <body className={font.className}>
                <SessionProvider session={session}>
                    <RolesContextProvider>
                        <ColorContextProvider theme={EngineerTheme}>
                            {children}
                        </ColorContextProvider>
                    </RolesContextProvider>
                </SessionProvider>
            </body>
        </html>
    );
}