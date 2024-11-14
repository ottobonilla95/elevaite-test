import {
  getContractObjectById,
  getContractProjectById,
  getContractProjectContracts,
} from "@repo/contracts-ui/actions";
import "./page.scss";
import { PdfAndExtraction } from "@repo/contracts-ui/components";
import {
  LoadingListObject,
  ContractObject,
} from "@repo/contracts-ui/interfaces";
import { redirect } from "next/navigation";

const mainViewString = encodeURIComponent("MainView");

export default async function ContractPage({
  params,
}: Readonly<{
  params: Promise<{
    projectId: string;
    fileId: string;
    secondaryFileId: string;
  }>;
}>) {
  const loading: LoadingListObject = {
    projects: undefined,
    contracts: true,
    submittingContract: false,
    projectReports: {},
    projectSettings: {},
    contractEmphasis: {},
    contractLineItems: {},
    contractVerification: {},
    deletingContract: false,
  };

  function getFilePromise(
    id: string
  ): [Promise<Response>, Promise<ContractObject>] | [undefined, undefined] {
    if (id === mainViewString) return [undefined, undefined];
    const CONTRACTS_URL = process.env.NEXT_PUBLIC_CONTRACTS_API_URL;
    const url = new URL(
      `${CONTRACTS_URL}/projects/${projectId}/files/${id}/file`
    );
    const contractPromise = getContractObjectById(projectId, id, false);
    const filePromise = fetch(url, { method: "GET" });
    return [filePromise, contractPromise];
  }

  const { projectId, fileId, secondaryFileId: secondaryFileId } = await params;
  if (isNaN(Number(secondaryFileId)) && secondaryFileId !== mainViewString)
    redirect(`/${projectId}/${fileId}/${mainViewString}`);

  const contractsListPromise = projectId
    ? getContractProjectContracts(projectId, false)
    : Promise.resolve([]);

  const [filePromise, contractPromise] = getFilePromise(fileId);
  const [secondaryFilePromise, secondaryContractPromise] = getFilePromise(
    secondaryFileId ? secondaryFileId : "0"
  );

  const [
    primaryContract,
    secondaryContract,
    fileRes,
    secondaryFileRes,
    contractsList,
  ] = await Promise.all([
    contractPromise,
    secondaryContractPromise,
    filePromise,
    secondaryFilePromise,
    contractsListPromise,
  ]);

  const file = await fileRes!.blob();
  // TODO remove secondary file completely in prod if not used
  const secondaryFile = await secondaryFileRes?.blob();

  const selectedProject = await getContractProjectById(projectId, false);

  return (
    <div className="contracts-main-container">
      <PdfAndExtraction
        file={file}
        loading={loading}
        projectId={projectId}
        selectedProject={selectedProject}
        selectedContract={primaryContract}
        secondarySelectedContract={secondaryContract}
        contractsList={contractsList}
      />
    </div>
  );
}
