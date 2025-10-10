import type { CardProps } from "@repo/ui/components";
import type { UserAccountMembershipObject } from "./app/lib/interfaces";

const ApplicationIcons = {
  applications: {
    supportBot: {
      src: "/icons/supportBot.svg",
      alt: "Chatbot",
    },
    dashboard: {
      src: "/icons/supportBot.svg",
      alt: "Dashboard",
    },
  },
};

const appLinks: Record<string, string> = {
  supportBot: "/chatbot",
  dashboard: "/analytics",
};

export function getApplications(
  _accountMemberships?: UserAccountMembershipObject[],
  userSession?: any // Add user session parameter
): { title: string; key: string; cards: CardProps[] }[] {
  const cards: CardProps[] = [];

  // Extract user role information from session
  const isAdmin = userSession?.user?.is_superuser === true || userSession?.user?.application_admin === true;
  const isManager = userSession?.user?.is_manager === true;
  const isFieldService = !isAdmin && !isManager; // Regular user (field service)

  // Chatbot tile - show to field service engineers and admins (not managers)
  if (isFieldService || isAdmin) {
    cards.push({
      icon: ApplicationIcons.applications.supportBot.src,
      description:
        "Please feel free to ask me anything. I'll do my best to provide helpful answers.",
      iconAlt: ApplicationIcons.applications.supportBot.alt,
      title: "Chatbot",
      link: appLinks.supportBot,
      id: "supportBot",
      miscLabel: "Version 2.0",
      subtitle: "By Toshiba",
      openInNewTab: false,
    });
  }

  // Dashboard tile - show to managers and admins (not field service)
  if (isManager || isAdmin) {
    cards.push({
      icon: ApplicationIcons.applications.dashboard.src,
      description:
        "View analytics, reports, and service performance metrics.",
      iconAlt: ApplicationIcons.applications.dashboard.alt,
      title: "Dashboard",
      link: appLinks.dashboard,
      id: "dashboard",
      miscLabel: "Version 1.0",
      subtitle: "By Toshiba",
      openInNewTab: false,
    });
  }

  return [
    {
      title: "Toshiba AI Assistants",
      key: "support",
      cards,
    },
  ];
}