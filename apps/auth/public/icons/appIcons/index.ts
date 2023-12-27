import slackIcon from "./slack.svg";
import onedriveIcon from "./oneDrive.svg";
import mongoDBIcon from "./mongoDB.svg";
import teamsIcon from "./teams.svg";
import supportBot from "./supportBot.svg";
import deckBuilder from "./deckBuilder.svg";
import insights from "./insights.svg";
import campaignBuilder from "./campaignBuilder.svg";

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
    deckBuilder: { src: (deckBuilder as SvgType).src, alt: "Deck Builder" },
    insights: { src: (insights as SvgType).src, alt: "ElevAIte Insights" },
    campaignBuilder: { src: (campaignBuilder as SvgType).src, alt: "Campaign Builder" },
  },
};
