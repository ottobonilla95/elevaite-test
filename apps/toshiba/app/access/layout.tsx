import { ElevaiteIcons, type SidebarIconObject } from "@repo/ui/components";
import { ColorContextProvider } from "@repo/ui/contexts";
import { RolesContextProvider } from "../lib/contexts/RolesContext";
import { ClientAppLayout } from "../ui/ClientAppLayout";
import { SessionProvider } from "next-auth/react";

const breadcrumbLabels: Record<string, { label: string; link: string }> = {
  access: {
    label: "Access Management",
    link: "/access",
  },
  home: {
    label: "Applications",
    link: "/",
  },
};

const sidebarIcons: SidebarIconObject[] = [
  {
    icon: <ElevaiteIcons.SVGAccess />,
    link: "/access",
    description: "Access Management",
  },
  {
    icon: <ElevaiteIcons.SVGApplications />,
    link: "/",
    description: "Applications",
  },
];

export default function AccessLayout({
  children,
}: {
  children: React.ReactNode;
}): JSX.Element {
  return (
    <SessionProvider>
      <RolesContextProvider>
        <ColorContextProvider>
          <ClientAppLayout
            breadcrumbLabels={breadcrumbLabels}
            sidebarIcons={sidebarIcons}
          >
            {children}
          </ClientAppLayout>
        </ColorContextProvider>
      </RolesContextProvider>
    </SessionProvider>
  );
}
