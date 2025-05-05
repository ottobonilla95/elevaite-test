import type { Metadata } from "next";


export const metadata: Metadata = {
    title: "ElevAIte Access Management",
    description: "View, add, and modify user roles and related access.",
};

export default function PageLayout({ children }: { children: React.ReactNode }): JSX.Element {
    return (
        <>
            {children}
        </>
    );
}