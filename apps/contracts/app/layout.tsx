import { Inter } from "next/font/google";
import "./layout.scss";
import "./layout.css"
import Providers from "./ui/Providers";
import { Metadata } from "next";
import { NavBar } from "@repo/ui/components";


const font = Inter({ subsets: ["latin"] });


interface RootLayoutProps {
    children: React.ReactNode
}

const breadcrumbLabels: Record<string, { label: string; link: string }> = {
  home: {
    label: "Applications",
    link: "/",
  }
};

export const metadata: Metadata = {
    title: "Contract Co-Pilot",
    description: "Quickly discover and evaluate important data in your contracts and invoices.",
};

export default function RootLayout({children}: RootLayoutProps): JSX.Element {

  async function handleSearchInput(term: string): Promise<void> {
    "use server"
  }

  async function logOut(): Promise<void> {
    "use server"
  }

    return (
        <html lang="en">
            <body className={font.className + " elevaite-main-container"}>
                <Providers>

                  <NavBar
                    breadcrumbLabels={breadcrumbLabels}
                    handleSearchInput={handleSearchInput}
                    logOut={logOut}
                    searchResults={[]}
                    user={undefined}
                  />
                  <div className="children-container">
                    {children}
                  </div>
                </Providers>
            </body>
        </html>
    );
}