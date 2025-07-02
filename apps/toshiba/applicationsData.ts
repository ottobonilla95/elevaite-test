import type { CardProps } from "@repo/ui/components";
import type { UserAccountMembershipObject } from "./app/lib/interfaces";

const ApplicationIcons = {
  applications: {
    supportBot: {
      src: "/icons/supportBot.svg",
      alt: "Chatbot",
    },
  },
};

const appLinks: Record<string, string> = {
  supportBot: "/chatbot",
};

export function getApplications(
  _accountMemberships?: UserAccountMembershipObject[]
): { title: string; key: string; cards: CardProps[] }[] {
  return [
    {
      title: "Toshiba AI Assistants",
      key: "support",
      cards: [
        {
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
        },
      ],
    },
  ];
}
