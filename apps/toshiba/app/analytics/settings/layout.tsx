import { ChatContextProvider } from "../ui/contexts/ChatContext";
import { AppLayout } from "../components/AppLayout";
import { SessionProvider } from "next-auth/react";
import { auth } from "../../../auth";

export default async function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>): Promise<JSX.Element> {
  const session = await auth();
  const breadcrumbs: Record<string, { label: string; link: string }> = {
    home: {
      label: "Settings",
      link: "/settings",
    },
  };

  return (
    <SessionProvider session={session}>
      {session ? (
        <ChatContextProvider>
          <AppLayout breadcrumbs={breadcrumbs}>{children}</AppLayout>
        </ChatContextProvider>
      ) : (
        <AppLayout breadcrumbs={breadcrumbs}>{children}</AppLayout>
      )}
    </SessionProvider>
  );
}

