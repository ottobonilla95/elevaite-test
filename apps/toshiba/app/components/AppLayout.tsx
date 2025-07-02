"use client";
import { NavBar } from "@repo/ui/components";
import { useSession } from "next-auth/react";
import type { ReactNode } from "react";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { logout } from "../lib/actions";
import "./AppLayout.scss";

interface AppLayoutProps {
  children: ReactNode;
  breadcrumbs: Record<string, { label: string; link: string }>;
}

export function AppLayout({
  children,
  breadcrumbs,
}: AppLayoutProps): JSX.Element {
  const [results, setResults] = useState<
    { key: string; link: string; label: string }[]
  >(getResults(""));
  const { data: session } = useSession();
  const router = useRouter();

  function getResults(
    term: string
  ): { key: string; link: string; label: string }[] {
    //TODO: implement search results
    // if (term) console.log("Searching for:", term);
    // console.log("Missing layout parameter");
    return [];
  }

  function handleSearchInput(term: string): void {
    setResults(getResults(term));
  }

  const additionalMenuItems = [
    {
      label: "Change Password",
      onClick: () => {
        router.push("/change-password");
      },
    },
  ];

  return (
    <div className="chatbot-layout-container">
      <NavBar
        breadcrumbLabels={breadcrumbs}
        handleSearchInput={handleSearchInput}
        logOut={logout}
        searchResults={results}
        user={{ image: session?.user?.image ?? "" }}
        additionalMenuItems={additionalMenuItems}
      />
      {children}
    </div>
  );
}
