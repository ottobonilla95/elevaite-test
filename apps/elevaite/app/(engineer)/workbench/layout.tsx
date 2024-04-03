import type { Metadata } from "next";


export const metadata: Metadata = {
    title: "ElevAIte Workbench",
    description: "Ingest and Preprocess data at your convenience.",
};

export default function PageLayout({ children }: { children: React.ReactNode }): JSX.Element {
    return (
        <>
            {children}
        </>
    );
}