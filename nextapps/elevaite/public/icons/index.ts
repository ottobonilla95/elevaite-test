import slackIcon from "./slack.svg";
import onedriveIcon from "./oneDrive.svg";
import mongoDBIcon from "./mongoDB.svg";
import teamsIcon from "./teams.svg";
import supportBot from "./supportBot.svg";
import deckBuilder from "./deckBuilder.svg";
import insights from "./insights.svg";
import campaignBuilder from "./campaignBuilder.svg";

export const ApplicationIcons = {
  workbench: {
    slack: { src: slackIcon.src, alt: "Slack" },
    oneDrive: { src: onedriveIcon.src, alt: "Onedrive" },
    mongoDB: { src: mongoDBIcon.src, alt: "MongoDB" },
    teams: { src: teamsIcon.src, alt: "Teams" },
  },
  applications: {
    supportBot: { src: supportBot.src, alt: "Support Bot" },
    deckBuilder: { src: deckBuilder.src, alt: "Deck Builder" },
    insights: { src: insights.src, alt: "ElevAIte Insights" },
    campaignBuilder: { src: campaignBuilder.src, alt: "Campaign Builder" },
  },
};
