import dayjs from "dayjs";
import { AppInstanceObject, AppInstanceStatus, ChartDataObject, PipelineStatus } from "./interfaces";




// export const TEST_CHART: ChartDataObject = {
//     totalItems: 178,
//     ingestedItems: 33,
//     avgSize: 2500/178,
//     totalSize: 2500,
//     ingestedSize: 480,
// }




export const TEST_INSTANCES: AppInstanceObject[] = [
    {
        creator: "Test User",
        datasetId: "Dataset Id Test 1",
        id: "Test Instance 1",
        startTime: dayjs().subtract(3, "days").toISOString(),
        status: AppInstanceStatus.RUNNING,
        selectedPipeline: "8470d675-6752-4446-8f07-fe7a99949e42",
        pipelineStatuses: [
            {
              step: "647427ef-2654-4585-8aaa-e03c66915c91",
              status: PipelineStatus.IDLE,
              startTime: "20240207T010111+0200",
              endTime: "20240207T010714+0200"
            }
        ]
    },
    {
        creator: "Random User 1",
        datasetId: "Dataset Id Test 2",
        id: "Test Instance 2",
        startTime: dayjs().subtract(2, "days").subtract(7, "hours").toISOString(),
        status: AppInstanceStatus.RUNNING,
        selectedPipeline: "8470d675-6752-4446-8f07-fe7a99949e42",
    },
    {
        creator: "Test User",
        datasetId: "Dataset Id Test 3",
        id: "Test Instance 3",
        startTime: dayjs().subtract(2, "days").subtract(7, "hours").toISOString(),
        endTime: dayjs().subtract(2, "days").subtract(5, "hours").subtract(25, "minutes").toISOString(),
        status: AppInstanceStatus.COMPLETED,
        selectedPipeline: "8470d675-6752-4446-8f07-fe7a99949e42",
    },
    {
        creator: "Random User 1",
        datasetId: "Dataset Id Test 4",
        id: "Test Instance 4",
        startTime: dayjs().subtract(2, "days").subtract(9, "hours").toISOString(),
        endTime: dayjs().subtract(2, "days").subtract(8, "hours").subtract(12, "minutes").toISOString(),
        status: AppInstanceStatus.COMPLETED,
        selectedPipeline: "8470d675-6752-4446-8f07-fe7a99949e42",
    },
    {
        creator: "Test User",
        datasetId: "Dataset Id Test 5",
        id: "Test Instance 5",
        startTime: dayjs().toISOString(),
        status: AppInstanceStatus.STARTING,
        selectedPipeline: "8470d675-6752-4446-8f07-fe7a99949e42",
    },
    {
        creator: "Test User",
        datasetId: "Dataset Id Test 6",
        id: "Test Instance 6",
        startTime: dayjs().subtract(11, "hours").toISOString(),
        endTime: dayjs().subtract(8, "hours").subtract(2, "minutes").toISOString(),
        status: AppInstanceStatus.FAILED,
        selectedPipeline: "8470d675-6752-4446-8f07-fe7a99949e42",
    },
];








