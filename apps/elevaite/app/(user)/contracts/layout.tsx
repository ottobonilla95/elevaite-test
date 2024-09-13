import type { Metadata } from "next";


export const metadata: Metadata = {
    title: "Contract Co-Pilot",
    description: "Quickly discover and evaluate important data in your contracts and invoices.",
};

export default function PageLayout({ children }: { children: React.ReactNode }): JSX.Element {
    return (
        <>
            {children}
        </>
    );
}