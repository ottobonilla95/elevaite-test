import type { CardProps } from "@repo/ui/components";
import { ApplicationIcons } from "./public/icons/appIcons";

const dummyDesc =
  "Mauris in quam ut neque scelerisque ultrices at eget nisl. Praesent a risus in orci porttitor commodo. Aenean condimentum luctus consequat. Sed volutpat metus quis libero molestie";

export const ingestionMethods: CardProps[] = [
  {
    icon: ApplicationIcons.workbench.slack.src,
    description: dummyDesc,
    iconAlt: ApplicationIcons.workbench.slack.alt,
    title: "Slack Ingest",
    subtitle: "By Elevaite",
    btnLabel: "Open",
    id: "SlackIngest001",
  },
  {
    icon: ApplicationIcons.workbench.oneDrive.src,
    description: dummyDesc,
    iconAlt: ApplicationIcons.workbench.oneDrive.alt,
    title: "One Drive Ingest",
    subtitle: "By Elevaite",
    btnLabel: "Open",
    id: "OneDrive001",
  },
  {
    icon: ApplicationIcons.workbench.mongoDB.src,
    description: dummyDesc,
    iconAlt: ApplicationIcons.workbench.mongoDB.alt,
    title: "MongoDB Ingest",
    subtitle: "By Elevaite",
    btnLabel: "Open",
    id: "MongoDB001",
  },
  {
    icon: ApplicationIcons.workbench.teams.src,
    description: dummyDesc,
    iconAlt: ApplicationIcons.workbench.teams.alt,
    title: "Microsoft Teams Ingest",
    subtitle: "By Elevaite",
    btnLabel: "Open",
    id: "Teams-001",
  },
  {
    icon: ApplicationIcons.workbench.slack.src,
    description: dummyDesc,
    iconAlt: ApplicationIcons.workbench.slack.alt,
    title: "Slack Ingest",
    subtitle: "By Elevaite",
    btnLabel: "Open",
    id: "Slack-001",
  },
  {
    icon: ApplicationIcons.workbench.oneDrive.src,
    description: dummyDesc,
    iconAlt: ApplicationIcons.workbench.oneDrive.alt,
    title: "One Drive Ingest",
    subtitle: "By Elevaite",
    btnLabel: "Open",
    id: "OneDrive-002",
  },
  {
    icon: ApplicationIcons.workbench.mongoDB.src,
    description: dummyDesc,
    iconAlt: ApplicationIcons.workbench.mongoDB.alt,
    title: "MongoDB Ingest",
    subtitle: "By Elevaite",
    btnLabel: "Open",
    id: "MongoDB-002",
  },
  {
    icon: ApplicationIcons.workbench.teams.src,
    description: dummyDesc,
    iconAlt: ApplicationIcons.workbench.teams.alt,
    title: "Microsoft Teams Ingest",
    subtitle: "By Elevaite",
    btnLabel: "Open",
    id: "Teams-002",
  },
];

const appLinks: Record<string, { development: string; production: string; test: string }> = {
  supportBot: {
    development: "http://localhost:3002",
    production: "https://elevaite-cb.iopex.ai/",
    test: "",
  },
  excletoppt: {
    development: "http://localhost:3003/homepage",
    production: "https://elevaite-apps.iopex.ai/askdocs ",
    test: "",
  },
  insights: {
    development: "https://arlo.opexwise.ai",
    production: "https://arlo.opexwise.ai",
    test: "",
  },
};

export function getApplications(
  env: "development" | "production" | "test"
): { title: string; key: string; cards: CardProps[] }[] {
  return [
    {
      title: "elevAIte for Support",
      key: "support",
      cards: [
        {
          icon: ApplicationIcons.applications.supportBot.src,
          description: "Please feel free to ask me anything. I'll do my best to provide helpful answers.",
          iconAlt: ApplicationIcons.applications.supportBot.alt,
          title: "Support Bot",
          link: appLinks.supportBot[env],
          id: "supportBot",
          miscLabel: "Version 2.0",
          subtitle: "By Elevaite",
        },
      ],
    },
    {
      title: "elevAIte for Finance",
      key: "finance",
      cards: [
        {
          icon: ApplicationIcons.applications.deckBuilder.src,
          description: "Convert your spreadsheets to presentations and ask questions",
          iconAlt: ApplicationIcons.applications.deckBuilder.alt,
          title: "AI Deck Builder",
          link: appLinks.excletoppt[env],
          id: "deckBuilder",
          miscLabel: "Version 2.0",
          subtitle: "By Elevaite",
        },
      ],
    },
    {
      title: "elevAIte for Revenue",
      key: "revenue",
      cards: [
        {
          icon: ApplicationIcons.applications.insights.src,
          description: "Your BI Application to make informed decisions. Data to Insights.",
          iconAlt: ApplicationIcons.applications.insights.alt,
          title: "elevAIte Insights",
          link: appLinks.insights[env],
          id: "insights",
          miscLabel: "Version 2.0",
          subtitle: "By Elevaite",
        },
        {
          icon: ApplicationIcons.applications.campaignBuilder.src,
          description: "Analyze attributes of past campaign metrics to build successful future campaigns.",
          iconAlt: ApplicationIcons.applications.campaignBuilder.alt,
          title: "AI Campaign Builder",
          id: "campaignBuilder",
          miscLabel: "Version 2.0",
          subtitle: "By Elevaite",
        },
      ],
    },
  ];
}
