import dayjs from "dayjs";
import { AppInstanceObject, AppInstanceStatus, ChartDataObject } from "./interfaces";




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
    },
    {
        creator: "Random User 1",
        datasetId: "Dataset Id Test 2",
        id: "Test Instance 2",
        startTime: dayjs().subtract(2, "days").subtract(7, "hours").toISOString(),
        status: AppInstanceStatus.RUNNING,
    },
    {
        creator: "Test User",
        datasetId: "Dataset Id Test 3",
        id: "Test Instance 3",
        startTime: dayjs().subtract(2, "days").subtract(7, "hours").toISOString(),
        endTime: dayjs().subtract(2, "days").subtract(5, "hours").subtract(25, "minutes").toISOString(),
        status: AppInstanceStatus.COMPLETED,
    },
    {
        creator: "Random User 1",
        datasetId: "Dataset Id Test 4",
        id: "Test Instance 4",
        startTime: dayjs().subtract(2, "days").subtract(9, "hours").toISOString(),
        endTime: dayjs().subtract(2, "days").subtract(8, "hours").subtract(12, "minutes").toISOString(),
        status: AppInstanceStatus.COMPLETED,
    },
    {
        creator: "Test User",
        datasetId: "Dataset Id Test 5",
        id: "Test Instance 5",
        startTime: dayjs().toISOString(),
        status: AppInstanceStatus.STARTING,
    },
    {
        creator: "Test User",
        datasetId: "Dataset Id Test 6",
        id: "Test Instance 6",
        startTime: dayjs().subtract(11, "hours").toISOString(),
        endTime: dayjs().subtract(8, "hours").subtract(2, "minutes").toISOString(),
        status: AppInstanceStatus.FAILED,
    },
];








