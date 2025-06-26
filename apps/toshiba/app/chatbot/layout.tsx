import { ColorContextProvider } from "@repo/ui/contexts";
import { ChatContextProvider } from "../ui/contexts/ChatContext";
import { AppLayout } from "../components/AppLayout";
import { SessionProvider } from "next-auth/react";
import { auth } from "../../auth";

export default async function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>): Promise<JSX.Element> {
  const session = await auth();
  const breadcrumbs: Record<string, { label: string; link: string }> = {
    home: {
      label: "Ask Toshiba",
      link: "/",
    },
  };

  return (
    <SessionProvider session={session}>
      <ColorContextProvider>
        {session ? (
          <ChatContextProvider session={session}>
            <AppLayout breadcrumbs={breadcrumbs}>{children}</AppLayout>
          </ChatContextProvider>
        ) : (
          <AppLayout breadcrumbs={breadcrumbs}>{children}</AppLayout>
        )}
      </ColorContextProvider>
    </SessionProvider>
  );
}
