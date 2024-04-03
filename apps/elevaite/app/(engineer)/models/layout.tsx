import type { Metadata } from "next";


export const metadata: Metadata = {
    title: "ElevAIte Models",
    description: "Find, organize, deploy, view, and edit models.",
};

export default function PageLayout({ children }: { children: React.ReactNode }): JSX.Element {
    return (
        <>
            {children}
        </>
    );
}