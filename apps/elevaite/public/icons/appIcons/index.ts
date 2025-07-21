import slackIcon from "./slack.svg";
import onedriveIcon from "./oneDrive.svg";
import mongoDBIcon from "./mongoDB.svg";
import teamsIcon from "./teams.svg";
import supportBot from "./supportBot.svg";
import deckBuilder from "./deckBuilder.svg";
import insights from "./insights.svg";
import campaignBuilder from "./campaignBuilder.svg";
import contracts from "./contracts.svg";
import analytics from "./analytics.svg";
import campaignOptimization from "./campaignOptimize.svg";    

interface SvgType {
  src: string;
}

export const ApplicationIcons = {
  workbench: {
    slack: { src: (slackIcon as SvgType).src, alt: "Slack" },
    oneDrive: { src: (onedriveIcon as SvgType).src, alt: "Onedrive" },
    mongoDB: { src: (mongoDBIcon as SvgType).src, alt: "MongoDB" },
    teams: { src: (teamsIcon as SvgType).src, alt: "Teams" },
  },
  applications: {
    supportBot: { src: (supportBot as SvgType).src, alt: "Support Bot" },
    arloSupport: { src: (supportBot as SvgType).src, alt: "Arlo Support Bot" },
    logsSupport: { src: (supportBot as SvgType).src, alt: "Logs Support Bot" },
    complianceSupport: { src: (supportBot as SvgType).src, alt: "Compliance Support Bot" },
    aleSupport: { src: (supportBot as SvgType).src, alt: "ALE Support Bot" },
    urlAssist: { src: (supportBot as SvgType).src, alt: "Website Support Bot" },
    deckBuilder: { src: (deckBuilder as SvgType).src, alt: "Deck Builder" },
    contracts: { src: (contracts as SvgType).src, alt: "Contract Co-Pilot" },
    contractsIopex: { src: (contracts as SvgType).src, alt: "Contract Co-Pilot for Iopex" },
    insights: { src: (insights as SvgType).src, alt: "ElevAIte Insights" },
    campaignBuilder: { src: (campaignBuilder as SvgType).src, alt: "Campaign Builder" },
    analytics: { src: (analytics as SvgType).src, alt: "Analytics Dashboard" },
    campaignOptimization: { src: (campaignOptimization as SvgType).src, alt: "Campaign Optimization" },    
  },
};
