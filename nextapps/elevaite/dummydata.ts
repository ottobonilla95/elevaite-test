import { WorkbenchCardProps } from "@elevaite/ui";
import slackIcon from "./public/ingestIcons/slack.svg";
import onedriveIcon from "./public/ingestIcons/oneDrive.svg";
import mongoDBIcon from "./public/ingestIcons/mongoDB.svg";
import teamsIcon from "./public/ingestIcons/teams.svg";

const dummyDesc =
  "Mauris in quam ut neque scelerisque ultrices at eget nisl. Praesent a risus in orci porttitor commodo. Aenean condimentum luctus consequat. Sed volutpat metus quis libero molestie";

export const ingestionMethods: WorkbenchCardProps[] = [
  { icon: slackIcon.src, description: dummyDesc, iconAlt: "Slack", title: "Slack Ingest", subtitle: "By Elevaite" },
  {
    icon: onedriveIcon.src,
    description: dummyDesc,
    iconAlt: "Onedrive",
    title: "One Drive Ingest",
    subtitle: "By Elevaite",
  },
  {
    icon: mongoDBIcon.src,
    description: dummyDesc,
    iconAlt: "MongoDB",
    title: "MongoDB Ingest",
    subtitle: "By Elevaite",
  },
  {
    icon: teamsIcon.src,
    description: dummyDesc,
    iconAlt: "Microsoft Teams",
    title: "Microsoft Teams Ingest",
    subtitle: "By Elevaite",
  },
  { icon: slackIcon.src, description: dummyDesc, iconAlt: "Slack", title: "Slack Ingest", subtitle: "By Elevaite" },
  {
    icon: onedriveIcon.src,
    description: dummyDesc,
    iconAlt: "Onedrive",
    title: "One Drive Ingest",
    subtitle: "By Elevaite",
  },
  {
    icon: mongoDBIcon.src,
    description: dummyDesc,
    iconAlt: "MongoDB",
    title: "MongoDB Ingest",
    subtitle: "By Elevaite",
  },
  {
    icon: teamsIcon.src,
    description: dummyDesc,
    iconAlt: "Microsoft Teams",
    title: "Microsoft Teams Ingest",
    subtitle: "By Elevaite",
  },
];
