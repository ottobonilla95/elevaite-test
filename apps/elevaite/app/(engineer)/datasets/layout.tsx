import type { Metadata } from "next";


export const metadata: Metadata = {
    title: "ElevAIte Datasets",
    description: "Find and download datasets.",
};

export default function PageLayout({ children }: { children: React.ReactNode }): JSX.Element {
    return (
        <>
            {children}
        </>
    );
}