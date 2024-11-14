import {
  getContractObjectById,
  getContractObjectEmphasis,
  getContractObjectLineItems,
  getContractProjectById,
  getContractProjectContracts,
} from "@repo/contracts-ui/actions";
import "./page.scss";
import { PdfAndExtraction } from "@repo/contracts-ui/components";
import {
  LoadingListObject,
  ContractObject,
  ContractObjectVerificationLineItem,
  ContractObjectEmphasis,
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

  function getContractPromises(
    id: string
  ):
    | [
        Promise<ContractObject>,
        Promise<ContractObjectVerificationLineItem[]>,
        Promise<ContractObjectEmphasis>,
      ]
    | [undefined, undefined, undefined, undefined] {
    if (id === mainViewString)
      return [undefined, undefined, undefined, undefined];
    const contractPromise = getContractObjectById(projectId, id, false);
    const lineItemsPromise = getContractObjectLineItems(projectId, id, false);
    const emphasisPromise = getContractObjectEmphasis(projectId, id, false);

    return [contractPromise, lineItemsPromise, emphasisPromise];
  }

  function updateContract(
    contract: ContractObject | undefined,
    lineItems: ContractObjectVerificationLineItem[] | undefined,
    emphasis: ContractObjectEmphasis | undefined
  ) {
    if (contract) {
      contract.line_items = lineItems;
      contract.highlight = emphasis;
    }
  }

  const { projectId, fileId, secondaryFileId: secondaryFileId } = await params;
  if (isNaN(Number(secondaryFileId)) && secondaryFileId !== mainViewString)
    redirect(`/${projectId}/${fileId}/${mainViewString}`);

  const contractsListPromise = projectId
    ? getContractProjectContracts(projectId, false)
    : Promise.resolve([]);

  const [contractPromise, lineItemsPromise, emphasisPromise] =
    getContractPromises(fileId);
  const [
    secondaryContractPromise,
    secondaryLineItemsPromise,
    secondaryEmphasisPromise,
  ] = getContractPromises(secondaryFileId ? secondaryFileId : "0");

  // Get file
  const CONTRACTS_URL = process.env.NEXT_PUBLIC_CONTRACTS_API_URL;
  const url = new URL(
    `${CONTRACTS_URL}/projects/${projectId}/files/${fileId}/file`
  );
  const filePromise = fetch(url, { method: "GET" });

  // Get contracts
  const [
    primaryContract,
    primaryLineItems,
    primaryEmphasis,
    fileRes,
    contractsList,
    secondaryContract,
    secondaryLineItems,
    secondaryEmphasis,
  ] = await Promise.all([
    contractPromise,
    lineItemsPromise,
    emphasisPromise,
    filePromise,
    contractsListPromise,
    secondaryContractPromise,
    secondaryLineItemsPromise,
    secondaryEmphasisPromise,
  ]);

  updateContract(primaryContract, primaryLineItems, primaryEmphasis);

  updateContract(secondaryContract, secondaryLineItems, secondaryEmphasis);

  const file = await fileRes!.blob();

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
