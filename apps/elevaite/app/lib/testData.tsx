import { AppInstanceStatus } from "./interfaces";




// export const TEST_CHART: ChartDataObject = {
//     totalItems: 178,
//     ingestedItems: 33,
//     avgSize: 2500/178,
//     totalSize: 2500,
//     ingestedSize: 480,
// }



export const testPipelineFlow = [
    {
        step: "Step 1",
        label: "Dataset ID URL",
        status: AppInstanceStatus.COMPLETED,
    },
    {
        step: "Step 2",
        label: "Extract Elements",
        status: AppInstanceStatus.COMPLETED,
    },
    {
        step: "Step 3",
        label: "Chunk Content",
        status: AppInstanceStatus.RUNNING,
    },
    {
        step: "Step 4",
        label: "Approve",
        status: AppInstanceStatus.STARTING,
    },
]



// export const TEST_INSTANCES: AppInstanceObject[] = [
//     {
//         creator: "Test User",
//         datasetId: "Dataset Id Test 1",
//         id: "Test Instance 1",
//         startTime: dayjs().subtract(3, "days").toISOString(),
//         status: AppInstanceStatus.RUNNING,
//         selectedPipeline: "8470d675-6752-4446-8f07-fe7a99949e42",
//         pipelineStepStatuses: [
//             {
//               step: "647427ef-2654-4585-8aaa-e03c66915c91",
//               status: PipelineStatus.IDLE,
//               startTime: "2024-02-10T19:30:38.000Z",
//               endTime: "2024-02-10T20:22:38.000Z"
//             }
//         ]
//     },
//     {
//         creator: "Random User 1",
//         datasetId: "Dataset Id Test 2",
//         id: "Test Instance 2",
//         startTime: dayjs().subtract(2, "days").subtract(7, "hours").toISOString(),
//         status: AppInstanceStatus.RUNNING,
//         selectedPipeline: "8470d675-6752-4446-8f07-fe7a99949e42",
//     },
//     {
//         creator: "Test User",
//         datasetId: "Dataset Id Test 3",
//         id: "Test Instance 3",
//         startTime: dayjs().subtract(2, "days").subtract(7, "hours").toISOString(),
//         endTime: dayjs().subtract(2, "days").subtract(5, "hours").subtract(25, "minutes").toISOString(),
//         status: AppInstanceStatus.COMPLETED,
//         selectedPipeline: "8470d675-6752-4446-8f07-fe7a99949e42",
//     },
//     {
//         creator: "Random User 1",
//         datasetId: "Dataset Id Test 4",
//         id: "Test Instance 4",
//         startTime: dayjs().subtract(2, "days").subtract(9, "hours").toISOString(),
//         endTime: dayjs().subtract(2, "days").subtract(8, "hours").subtract(12, "minutes").toISOString(),
//         status: AppInstanceStatus.COMPLETED,
//         selectedPipeline: "8470d675-6752-4446-8f07-fe7a99949e42",
//     },
//     {
//         creator: "Test User",
//         datasetId: "Dataset Id Test 5",
//         id: "Test Instance 5",
//         startTime: dayjs().toISOString(),
//         status: AppInstanceStatus.STARTING,
//         selectedPipeline: "8470d675-6752-4446-8f07-fe7a99949e42",
//     },
//     {
//         creator: "Test User",
//         datasetId: "Dataset Id Test 6",
//         id: "Test Instance 6",
//         startTime: dayjs().subtract(11, "hours").toISOString(),
//         endTime: dayjs().subtract(8, "hours").subtract(2, "minutes").toISOString(),
//         status: AppInstanceStatus.FAILED,
//         selectedPipeline: "8470d675-6752-4446-8f07-fe7a99949e42",
//     },
// ];








