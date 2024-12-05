import { ContractsBreadcrumbs } from "@repo/contracts-ui/components";
import { NavBar } from "@repo/ui/components";
import { type Metadata } from "next";
import { Inter } from "next/font/google";
import Providers from "../ui/Providers";
import "./layout.scss";

const font = Inter({ subsets: ["latin"] });



interface RootLayoutProps {
  children: React.ReactNode;
}


export const metadata: Metadata = {
  title: "Contract Co-Pilot",
  description: "Quickly discover and evaluate important data in your contracts and invoices.",
};

export default function RootLayout({ children }: RootLayoutProps): JSX.Element {
  // eslint-disable-next-line @typescript-eslint/require-await -- temp
  async function handleSearchInput(term: string): Promise<void> {
    "use server";
  }

  // eslint-disable-next-line @typescript-eslint/require-await -- temp
  async function logOut(): Promise<void> {
    "use server";
  }

  return (
    <html lang="en">
      <body className={`${font.className} elevaite-main-container`}>
        <Providers>
          <NavBar
            customBreadcrumbs={<ContractsBreadcrumbs/>}
            handleSearchInput={handleSearchInput}
            logOut={logOut}
            searchResults={[]}
            user={undefined}
          />
          <div className="children-container">{children}</div>
        </Providers>
      </body>
    </html>
  );
}
