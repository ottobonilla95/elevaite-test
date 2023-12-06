import { CardProps } from "@elevaite/ui";
import { ApplicationIcons } from "./public/icons";

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
  },
  {
    icon: ApplicationIcons.workbench.oneDrive.src,
    description: dummyDesc,
    iconAlt: ApplicationIcons.workbench.oneDrive.alt,
    title: "One Drive Ingest",
    subtitle: "By Elevaite",
    btnLabel: "Open",
  },
  {
    icon: ApplicationIcons.workbench.mongoDB.src,
    description: dummyDesc,
    iconAlt: ApplicationIcons.workbench.mongoDB.alt,
    title: "MongoDB Ingest",
    subtitle: "By Elevaite",
    btnLabel: "Open",
  },
  {
    icon: ApplicationIcons.workbench.teams.src,
    description: dummyDesc,
    iconAlt: ApplicationIcons.workbench.teams.alt,
    title: "Microsoft Teams Ingest",
    subtitle: "By Elevaite",
    btnLabel: "Open",
  },
  {
    icon: ApplicationIcons.workbench.slack.src,
    description: dummyDesc,
    iconAlt: ApplicationIcons.workbench.slack.alt,
    title: "Slack Ingest",
    subtitle: "By Elevaite",
    btnLabel: "Open",
  },
  {
    icon: ApplicationIcons.workbench.oneDrive.src,
    description: dummyDesc,
    iconAlt: ApplicationIcons.workbench.oneDrive.alt,
    title: "One Drive Ingest",
    subtitle: "By Elevaite",
    btnLabel: "Open",
  },
  {
    icon: ApplicationIcons.workbench.mongoDB.src,
    description: dummyDesc,
    iconAlt: ApplicationIcons.workbench.mongoDB.alt,
    title: "MongoDB Ingest",
    subtitle: "By Elevaite",
    btnLabel: "Open",
  },
  {
    icon: ApplicationIcons.workbench.teams.src,
    description: dummyDesc,
    iconAlt: ApplicationIcons.workbench.teams.alt,
    title: "Microsoft Teams Ingest",
    subtitle: "By Elevaite",
    btnLabel: "Open",
  },
];

const appLinks = {
  supportBot: {
    development: "http://localhost:3002",
    production: "https://elevaite-cb.iopex.ai/",
  },
  excletoppt: {
    development: "http://localhost:3003",
    production: "https://elevaite-apps.iopex.ai/askdocs ",
  },
  insights: {
    development: "http://localhost:3004",
    production: "https://arlo.opexwise.ai/",
  },
};

export const applications = [
  {
    title: "elevAIte for Support",
    key: "support",
    cards: [
      {
        icon: ApplicationIcons.applications.supportBot.src,
        description: "Please feel free to ask me anything. I'll do my best to provide helpful answers.",
        iconAlt: ApplicationIcons.applications.supportBot.alt,
        title: "Support Bot",
        link: appLinks.supportBot[process.env.NODE_ENV],
        id: "supportBot",
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
        link: appLinks.excletoppt[process.env.NODE_ENV],
        id: "deckBuilder",
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
        link: appLinks.insights[process.env.NODE_ENV],
        id: "insights",
      },
      {
        icon: ApplicationIcons.applications.campaignBuilder.src,
        description: "Analyze attributes of past campaign metrics to build successful future campaigns.",
        iconAlt: ApplicationIcons.applications.campaignBuilder.alt,
        title: "AI Campaign Builder",
        id: "campaignBuilder",
      },
    ],
  },
];
