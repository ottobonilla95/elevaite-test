import {
  getContractObjectById,
  getContractProjectContracts,
} from "@/lib/actions/contractActions";
import "./page.scss";
import { PdfAndExtraction } from "@/components/PdfAndExtraction";

export default async function ContractPage({
  params,
}: Readonly<{ params: Promise<{ projectId: string; fileId: string }> }>) {
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

  const [contract, contractsList, fileRes] = await Promise.all([
    contractPromise,
    contractsListPromise,
    filePromise,
  ]);

  const file = await fileRes.blob();

  return (
    <div className="contracts-main-container">
      <PdfAndExtraction
        fileId={fileId}
        projectId={projectId}
        contractsList={contractsList}
        contract={contract}
        file={file}
      />
    </div>
  );
}
