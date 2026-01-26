"use server";
import { SessionProvider } from "next-auth/react";
import { auth } from "../../auth";

interface SessionWrapperProps {
  children?: React.ReactNode;
}

export async function SessionWrapper({
  children,
}: SessionWrapperProps): Promise<JSX.Element> {
  // In development mode, provide a mock session
  if (process.env.NODE_ENV === "development") {
    const mockSession = {
      user: {
        id: "dev-user-id",
        name: "Development User",
        email: "dev@example.com",
        image: null,
        // Add any other required fields for development
        accountMemberships: [
          {
            account_id: "dev-account-id",
            account_name: "Development Account",
            is_admin: false,
            roles: [
              {
                id: "dev-role-id",
                name: "Developer",
              },
            ],
          },
        ],
      },
      expires: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(), // 24 hours from now
    };

    return <SessionProvider session={mockSession}>{children}</SessionProvider>;
  }

  // Production mode - use real auth
  const session = await auth();

  if (session?.user) {
    // filter out sensitive data before passing to client.
    // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment -- Filtering sensitive session data
    session.user = {
      id: session.user.id,
      name: session.user.name,
      email: session.user.email,
      image: session.user.image,
      // Preserve accountMemberships if they exist
      ...(session.user.accountMemberships && {
        // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment -- Preserving accountMemberships
        accountMemberships: session.user.accountMemberships,
      }),
    };
  }

  return <SessionProvider session={session}>{children}</SessionProvider>;
}
