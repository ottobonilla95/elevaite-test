import {
  getContractObjectById,
  getContractObjectEmphasis,
  getContractObjectLineItems,
  getContractObjectVerification,
  getContractProjectById,
  getContractProjectContracts,
  getContractProjectSettings,
} from "@repo/contracts-ui/actions";
import "./page.scss";
import { PdfAndExtraction } from "@repo/contracts-ui/components";
import {
  LoadingListObject,
  ContractObject,
  ContractObjectVerificationLineItem,
  ContractObjectEmphasis,
  ContractObjectVerification,
} from "@repo/contracts-ui/interfaces";
import { redirect } from "next/navigation";

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
        Promise<ContractObjectVerification>,
      ]
    | [undefined, undefined, undefined, undefined] {
    if (id === "0") return [undefined, undefined, undefined, undefined];
    const contractPromise = getContractObjectById(projectId, id);
    const lineItemsPromise = getContractObjectLineItems(projectId, id);
    const emphasisPromise = getContractObjectEmphasis(projectId, id);
    const verificationPromise = getContractObjectVerification(projectId, id);

    return [
      contractPromise,
      lineItemsPromise,
      emphasisPromise,
      verificationPromise,
    ];
  }

  function updateContractAndProject(
    contract: ContractObject | undefined,
    lineItems: ContractObjectVerificationLineItem[] | undefined,
    emphasis: ContractObjectEmphasis | undefined,
    verification: ContractObjectVerification | undefined
  ) {
    if (contract) {
      contract.line_items = lineItems;
      contract.highlight = emphasis;
      contract.verification = verification;
      if (lineItems) {
        loading.contractLineItems = {
          ...loading.contractLineItems,
          [contract.id]: false,
        };
      }

      if (verification) {
        loading.contractVerification = {
          ...loading.contractVerification,
          [contract.id]: false,
        };
      }

      if (emphasis) {
        loading.contractEmphasis = {
          ...loading.contractEmphasis,
          [contract.id]: false,
        };
      }
    }
  }

  const { projectId, fileId, secondaryFileId } = await params;
  if (isNaN(Number(secondaryFileId)) && secondaryFileId !== "0")
    redirect(`/${projectId}/${fileId}/compare/0`);

  const contractsListPromise = projectId
    ? getContractProjectContracts(projectId)
    : Promise.resolve([]);

  // Get file
  const CONTRACTS_URL = process.env.NEXT_PUBLIC_CONTRACTS_API_URL;
  const url = new URL(
    `${CONTRACTS_URL}/projects/${projectId}/files/${fileId}/file`
  );
  const filePromise = fetch(url, { method: "GET" });

  // Get contracts
  const [
    contractPromise,
    lineItemsPromise,
    emphasisPromise,
    verificationPromise,
  ] = getContractPromises(fileId);

  const [
    secondaryContractPromise,
    secondaryLineItemsPromise,
    secondaryEmphasisPromise,
    secondaryVerificationPromise,
  ] = getContractPromises(secondaryFileId ? secondaryFileId : "0");

  // Get project
  const projectPromise = getContractProjectById(projectId);
  const settingsPromise = getContractProjectSettings(projectId);

  const [
    primaryContract,
    primaryLineItems,
    primaryEmphasis,
    primaryVerification,
    fileRes,
    contractsList,
    secondaryContract,
    secondaryLineItems,
    secondaryEmphasis,
    secondaryVerification,
    project,
    settings,
  ] = await Promise.all([
    contractPromise,
    lineItemsPromise,
    emphasisPromise,
    verificationPromise,
    filePromise,
    contractsListPromise,
    secondaryContractPromise,
    secondaryLineItemsPromise,
    secondaryEmphasisPromise,
    secondaryVerificationPromise,
    projectPromise,
    settingsPromise,
  ]);

  updateContractAndProject(
    primaryContract,
    primaryLineItems,
    primaryEmphasis,
    primaryVerification
  );

  updateContractAndProject(
    secondaryContract,
    secondaryLineItems,
    secondaryEmphasis,
    secondaryVerification
  );

  if (settings) {
    loading.projectSettings = {
      ...loading.projectSettings,
      [project.id]: false,
    };
  }

  const file = await fileRes!.blob();

  return (
    <div className="contracts-main-container">
      <PdfAndExtraction
        file={file}
        loading={loading}
        projectId={projectId}
        selectedProject={project}
        selectedContract={primaryContract}
        secondarySelectedContract={secondaryContract}
        contractsList={contractsList}
        comparisonScreen
      />
    </div>
  );
}
