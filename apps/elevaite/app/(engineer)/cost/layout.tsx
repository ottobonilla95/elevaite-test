import type { Metadata } from "next";


export const metadata: Metadata = {
    title: "ElevAIte Billing and Costs Management",
    description: "An overview of all costs and billing options.",
};

export default function PageLayout({ children }: { children: React.ReactNode }): JSX.Element {
    return (
        <>
            {children}
        </>
    );
}