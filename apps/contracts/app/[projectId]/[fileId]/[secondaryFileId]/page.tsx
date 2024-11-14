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
  ContractSettings,
  ContractProjectObject,
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
        Promise<ContractObjectVerification>,
        Promise<ContractSettings>,
      ]
    | [undefined, undefined, undefined, undefined] {
    if (id === mainViewString)
      return [undefined, undefined, undefined, undefined];
    const contractPromise = getContractObjectById(projectId, id, false);
    const lineItemsPromise = getContractObjectLineItems(projectId, id, false);
    const emphasisPromise = getContractObjectEmphasis(projectId, id, false);
    const verificationPromise = getContractObjectVerification(
      projectId,
      id,
      false
    );
    const settingsPromise = getContractProjectSettings(projectId, false);

    return [
      contractPromise,
      lineItemsPromise,
      emphasisPromise,
      verificationPromise,
      settingsPromise,
    ];
  }

  function updateContractAndProject(
    project: ContractProjectObject,
    contract: ContractObject | undefined,
    lineItems: ContractObjectVerificationLineItem[] | undefined,
    emphasis: ContractObjectEmphasis | undefined,
    verification: ContractObjectVerification | undefined,
    settings: ContractSettings | undefined
  ) {
    project.settings = settings;

    if (settings) {
      loading.projectSettings = {
        ...loading.projectSettings,
        [project.id]: false,
      };
    }

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

  const { projectId, fileId, secondaryFileId: secondaryFileId } = await params;
  if (isNaN(Number(secondaryFileId)) && secondaryFileId !== mainViewString)
    redirect(`/${projectId}/${fileId}/${mainViewString}`);

  const contractsListPromise = projectId
    ? getContractProjectContracts(projectId, false)
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
    settingsPromise,
  ] = getContractPromises(fileId);
  const [
    secondaryContractPromise,
    secondaryLineItemsPromise,
    secondaryEmphasisPromise,
    secondaryVerificationPromise,
    secondarySettingsPromise,
  ] = getContractPromises(secondaryFileId ? secondaryFileId : "0");

  const [
    primaryContract,
    primaryLineItems,
    primaryEmphasis,
    primaryVerification,
    primarySettings,
    fileRes,
    contractsList,
    secondaryContract,
    secondaryLineItems,
    secondaryEmphasis,
    secondaryVerification,
    secondarySettings,
  ] = await Promise.all([
    contractPromise,
    lineItemsPromise,
    emphasisPromise,
    verificationPromise,
    settingsPromise,
    filePromise,
    contractsListPromise,
    secondaryContractPromise,
    secondaryLineItemsPromise,
    secondaryEmphasisPromise,
    secondaryVerificationPromise,
    secondarySettingsPromise,
  ]);

  const selectedProject = await getContractProjectById(projectId, false);

  updateContractAndProject(
    selectedProject,
    primaryContract,
    primaryLineItems,
    primaryEmphasis,
    primaryVerification,
    primarySettings
  );

  updateContractAndProject(
    selectedProject,
    secondaryContract,
    secondaryLineItems,
    secondaryEmphasis,
    secondaryVerification,
    primarySettings
  );

  const file = await fileRes!.blob();

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
