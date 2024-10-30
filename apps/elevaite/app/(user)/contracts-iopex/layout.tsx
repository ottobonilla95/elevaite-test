import type { Metadata } from "next";


export const metadata: Metadata = {
    title: "Contract Co-Pilot for Iopex",
    description: "Quickly discover and approve contracts, invoices and POs.",
};

export default function PageLayout({ children }: { children: React.ReactNode }): JSX.Element {
    return (
        <>
            {children}
        </>
    );
}