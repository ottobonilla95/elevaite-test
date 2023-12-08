import datasetsIcon from "./datasets.svg";
import modelsIcon from "./models.svg";
import workbenchIcon from "./workbench.svg";
import workersQueuesIcons from "./workers-queues.svg";

export const SidebarIcons: { [key: string]: { src: string; alt: string } } = {
  datasets: { src: datasetsIcon.src, alt: "Datasets" },
  models: { src: modelsIcon.src, alt: "Models" },
  workbench: { src: workbenchIcon.src, alt: "Workbench" },
  workers_queues: { src: workersQueuesIcons.src, alt: "Workers & Queues" },
};
