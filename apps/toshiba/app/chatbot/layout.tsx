import { ColorContextProvider } from "@repo/ui/contexts";
import { ChatContextProvider } from "../ui/contexts/ChatContext";
import { AppLayout } from "../components/AppLayout";

import { SessionProvider } from "next-auth/react";

// eslint-disable-next-line @typescript-eslint/require-await -- pretty sure this has to be async
export default async function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>): Promise<JSX.Element> {
  const breadcrumbs: Record<string, { label: string; link: string }> = {
    home: {
      label: "Ask Toshiba",
      link: "/",
    },
  };

  return (
    <SessionProvider>
      <ColorContextProvider>
        <ChatContextProvider>
          <AppLayout breadcrumbs={breadcrumbs}>{children}</AppLayout>
        </ChatContextProvider>
      </ColorContextProvider>
    </SessionProvider>
  );
}
