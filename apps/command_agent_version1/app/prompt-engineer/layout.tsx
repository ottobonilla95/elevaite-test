import { Metadata } from "next";
import { PromptContextProvider } from "../ui/contexts/PromptContext";

export const metadata: Metadata = {
  title: "Agentic AI - Prompts Engineer",
  description: "Your control room for your prompts",
};

export default async function Layout({ children, }: Readonly<{ children: React.ReactNode; }>): Promise<JSX.Element> {

    return (
        <PromptContextProvider>
            {children}
        </PromptContextProvider>
    )
}