"use client";
import { NavBar } from "@repo/ui/components";
import { useSession } from "next-auth/react";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { HomeIcon } from "./icons/HomeIcon";

interface AppLayoutProps {
  children: React.ReactNode;
  breadcrumbs: Record<string, { label: string; link: string }>;
}

export function AppLayout({
  children,
  breadcrumbs,
}: AppLayoutProps): JSX.Element {
  const { data: session } = useSession();
  const pathname = usePathname();
  const [currentBreadcrumb, setCurrentBreadcrumb] = useState<string | null>(
    null
  );

  useEffect(() => {
    const pathParts = pathname.split("/").filter(Boolean);
    const lastPart = pathParts[pathParts.length - 1] || "home";
    setCurrentBreadcrumb(lastPart);
  }, [pathname]);

  const navbarButtons = [
    {
      id: "home",
      label: "Home",
      icon: <HomeIcon />,
      link: "/",
    },
  ];

  const [searchResults, setSearchResults] = useState<
    { key: string; link: string; label: string }[]
  >([]);

  const handleSearchInput = (term: string): void => {
    // Simple search implementation
    const results = [
      { key: "home", link: "/", label: "Pipeline Home" },
      { key: "parsing", link: "/parsing", label: "Parsing Step" },
      { key: "chunking", link: "/chunking", label: "Chunking Step" },
      { key: "embedding", link: "/embedding", label: "Embedding Step" },
      { key: "indexing", link: "/indexing", label: "Indexing Step" },
      { key: "retrieval", link: "/retrieval", label: "Retrieval Step" },
    ].filter((item) => item.label.toLowerCase().includes(term.toLowerCase()));
    setSearchResults(results);
  };

  const logOut = async (): Promise<void> => {
    // Implement logout functionality
    window.location.href = "/api/auth/signout";
  };

  return (
    <div className="min-h-screen flex flex-col">
      <NavBar
        breadcrumbLabels={breadcrumbs}
        handleSearchInput={handleSearchInput}
        searchResults={searchResults}
        logOut={logOut}
        user={session?.user}
      />
      <main
        className="flex-grow"
        style={{ paddingTop: "var(--navbar-height)" }}
      >
        {children}
      </main>
    </div>
  );
}
