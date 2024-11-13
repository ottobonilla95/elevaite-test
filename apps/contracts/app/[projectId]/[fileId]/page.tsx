import {
  getContractObjectById,
  getContractProjectContracts,
} from "@repo/contracts-ui/actions";
import "./page.scss";
import { PdfAndExtraction } from "@repo/contracts-ui/components";
import { LoadingListObject } from "@repo/contracts-ui/interfaces";

export default async function ContractPage({
  params,
}: Readonly<{ params: Promise<{ projectId: string; fileId: string }> }>) {
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

  const { projectId, fileId } = await params;

  const contractPromise = getContractObjectById(projectId, fileId, false);
  const contractsListPromise = projectId
    ? getContractProjectContracts(projectId, false)
    : Promise.resolve([]);

  //   const url = new URL(`/api/contracts/`);
  //   url.searchParams.set("projectId", projectId);
  //   url.searchParams.set("contractId", fileId);
  const CONTRACTS_URL = process.env.NEXT_PUBLIC_CONTRACTS_API_URL;
  const url = new URL(
    `${CONTRACTS_URL}/projects/${projectId}/files/${fileId}/file`
  );
  const filePromise = fetch(url, { method: "GET" });

  const [primaryContract, contractsList, fileRes] = await Promise.all([
    contractPromise,
    contractsListPromise,
    filePromise,
  ]);

  const file = await fileRes.blob();

  return (
    <div className="contracts-main-container">
      <PdfAndExtraction
        file={file}
        loading={loading}
        projectId={projectId}
        primarycontract={primaryContract}
        contractsList={contractsList}
      />
    </div>
  );
}
