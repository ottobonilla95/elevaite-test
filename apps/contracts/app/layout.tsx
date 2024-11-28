import { Inter } from "next/font/google";
import "./layout.scss";
import "./layout.css";
import { type Metadata } from "next";
import { NavBar } from "@repo/ui/components";
import Providers from "../ui/Providers";

const font = Inter({ subsets: ["latin"] });

interface RootLayoutProps {
  children: React.ReactNode;
}

const breadcrumbLabels: Record<string, { label: string; link: string }> = {
  home: {
    label: "Applications",
    link: "/",
  },
};

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
            breadcrumbLabels={breadcrumbLabels}
            hideBreadcrumbs
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
