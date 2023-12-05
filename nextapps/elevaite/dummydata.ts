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

export const applications: { [key: string]: CardProps } = {
  supportBot: {
    icon: ApplicationIcons.applications.supportBot.src,
    description: "Please feel free to ask me anything. I'll do my best to provide helpful answers.",
    iconAlt: ApplicationIcons.applications.supportBot.alt,
    title: "Support Bot",
    subtitle: "By Elevaite",
    btnLabel: "Documentation",
  },
  deckBuilder: {
    icon: ApplicationIcons.applications.deckBuilder.src,
    description: "Convert your spreadsheets to presentations and ask questions",
    iconAlt: ApplicationIcons.applications.deckBuilder.alt,
    title: "AI Deck Builder",
    subtitle: "By Elevaite",
    btnLabel: "Documentation",
  },
  insights: {
    icon: ApplicationIcons.applications.insights.src,
    description: "Your BI Application to make informed decisions. Data to Insights.",
    iconAlt: ApplicationIcons.applications.insights.alt,
    title: "ElevAIte Insights",
    subtitle: "By Elevaite",
    btnLabel: "Documentation",
  },
  campaignBuilder: {
    icon: ApplicationIcons.applications.campaignBuilder.src,
    description: "Analyze attributes of past campaign metrics to build successful future campaigns.",
    iconAlt: ApplicationIcons.applications.campaignBuilder.alt,
    title: "AI Campaign Builder",
    subtitle: "By Elevaite",
    btnLabel: "Documentation",
  },
};
