"use server";
import { SessionProvider } from "next-auth/react";
import { auth } from "../../auth";


interface SessionWrapperProps {
    children?: React.ReactNode;
}

export async function SessionWrapper({children}: SessionWrapperProps): Promise<JSX.Element> {
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
        <SessionProvider session={session}>
            {children}
        </SessionProvider>
    );
}