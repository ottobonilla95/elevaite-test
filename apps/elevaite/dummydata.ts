import type { CardProps } from "@repo/ui/components";
import { ApplicationIcons } from "./public/icons/appIcons";
import { UserAccountMembershipObject } from "./app/lib/interfaces";

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
  arloSupport: {
    development: "https://elevaite-arlocb.iopex.ai",
    production: "https://elevaite-arlocb.iopex.ai",
    test: "",
  },
  logsSupport: {
    development: "https://elevaite-logs.iopex.ai",
    production: "https://elevaite-logs.iopex.ai",
    test: "",
  },
  complianceSupport: {
    development: "http://elevaite-vmcb-api.iopex.ai/",
    production: "http://elevaite-vmcb-api.iopex.ai/",
    test: "",
  },
  aleSupport: {
    development: "https://elevaite-alcb-api.iopex.ai",
    production: "https://elevaite-alcb-api.iopex.ai",
    test: "",
  },
  supportBot: {
    development: "http://localhost:3002",
    production: "https://elevaite-cb.iopex.ai/",
    test: "",
  },
  excletoppt: {
    development: "http://localhost:3003/homepage",
    production: "https://elevaite-test.iopex.ai/homepage",
    test: "",
  },
  insights: {
    development: "https://arlo.opexwise.ai",
    production: "https://arlo.opexwise.ai",
    test: "",
  },
  contracts: {
    development: "/contracts",
    production: "/contracts",
    test: "",
  },
  contractsIopex: {
    development: "/contracts-iopex",
    production: "/contracts-iopex",
    test: "",
  },
  mediaplan: {
    development: "http://localhost:3004/homepage",
    production: "http://localhost:3004/homepage",
    test: "",
  }
};

export function getApplications(
  env: "development" | "production" | "test", accountMemberships?: UserAccountMembershipObject[]
): { title: string; key: string; cards: CardProps[] }[] {
  if (accountMemberships) {
    let isAlcatel = false
    console.log(accountMemberships)
    accountMemberships.forEach((membership) => {
      if (membership.account_id === "ab5eed01-46f1-423d-9da0-093814a898fc") {
        isAlcatel = true
      }
    })
    // eslint-disable-next-line @typescript-eslint/no-unnecessary-condition -- No it's not
    if (isAlcatel) return [
      {
        title: "elevAIte for Support",
        key: "support",
        cards: [
          {
            icon: ApplicationIcons.applications.aleSupport.src,
            description: "Your guide for precise Networking and Communication Answers!",
            iconAlt: ApplicationIcons.applications.aleSupport.alt,
            title: "ALE - Tech Chat Support",
            link: appLinks.complianceSupport[env],
            id: "aleSupport",
            miscLabel: "Version 1.0",
            subtitle: "By Elevaite",
            openInNewTab: true,
          },
        ],
      },
      {
        title: "elevAIte for Finance",
        key: "finance",
        cards: [],
      },
      {
        title: "elevAIte for Revenue",
        key: "revenue",
        cards: [],
      },
    ];
  }
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
          openInNewTab: true,
        },
        {
          icon: ApplicationIcons.applications.arloSupport.src,
          description: "Your AI-powered Bot guiding you through setup, troubleshooting, and to answer your product related queries.",
          iconAlt: ApplicationIcons.applications.arloSupport.alt,
          title: "Arlo Support",
          link: appLinks.arloSupport[env],
          id: "arloSupport",
          miscLabel: "Version 2.0",
          subtitle: "By Elevaite",
          openInNewTab: true,
        },
        {
          icon: ApplicationIcons.applications.logsSupport.src,
          description: "Your AI-powered Bot to guide you through the log analysis.",
          iconAlt: ApplicationIcons.applications.logsSupport.alt,
          title: "Logs Support",
          link: appLinks.logsSupport[env],
          id: "logsSupport",
          miscLabel: "Version 2.0",
          subtitle: "By Elevaite",
          openInNewTab: true,
        },
        {
          icon: ApplicationIcons.applications.complianceSupport.src,
          description: "Your Partner in SLA Success - Help verify and resolve your vendor related queries.",
          iconAlt: ApplicationIcons.applications.complianceSupport.alt,
          title: "Compliance Support",
          link: appLinks.complianceSupport[env],
          id: "complianceSupport",
          miscLabel: "Version 1.0",
          subtitle: "By Elevaite",
          openInNewTab: true,
        },
        {
          icon: ApplicationIcons.applications.aleSupport.src,
          description: "Your guide for precise Networking and Communication Answers!",
          iconAlt: ApplicationIcons.applications.aleSupport.alt,
          title: "ALE - Tech Chat Support",
          link: appLinks.complianceSupport[env],
          id: "aleSupport",
          miscLabel: "Version 1.0",
          subtitle: "By Elevaite",
          openInNewTab: true,
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
          title: "Deck Builder",
          link: appLinks.excletoppt[env],
          id: "deckBuilder",
          miscLabel: "Version 2.0",
          subtitle: "By Elevaite",
          openInNewTab: true,
        },
        {
          icon: ApplicationIcons.applications.contracts.src,
          description: "Quickly discover and evaluate important data in your contracts and invoices",
          iconAlt: ApplicationIcons.applications.contracts.alt,
          title: "Contract Co-Pilot",
          link: appLinks.contracts[env],
          id: "contracts",
          miscLabel: "Version 1.0",
          subtitle: "By Elevaite",
          openInNewTab: false,
        },
        {
          icon: ApplicationIcons.applications.contractsIopex.src,
          description: " Quickly discover and approve contracts, invoices and PO's",
          iconAlt: ApplicationIcons.applications.contractsIopex.alt,
          title: "Contract Co-Pilot (iOPEX)",
          link: appLinks.contractsIopex[env],
          id: "contractsIopex",
          miscLabel: "Version 1.0",
          subtitle: "By Elevaite",
          openInNewTab: false,
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
          openInNewTab: true,
        },
        {
          icon: ApplicationIcons.applications.campaignBuilder.src,
          description: "Analyze creatives, generate tailored media plans, and unlock insights from your creative data.",
          iconAlt: ApplicationIcons.applications.campaignBuilder.alt,
          title: "Media and Marketing",
          link: appLinks.mediaplan[env],
          id: "mediaplan",
          miscLabel: "Version 1.0",
          subtitle: "By Elevaite",
          openInNewTab: true,
        },
      ],
    },
  ];
}
