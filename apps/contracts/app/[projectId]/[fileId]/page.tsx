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
import { LoadingListObject } from "@repo/contracts-ui/interfaces";

export default async function ContractPage({
  params,
}: Readonly<{
  params: Promise<{
    projectId: string;
    fileId: string;
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

  const { projectId, fileId } = await params;

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
  const contractPromise = getContractObjectById(projectId, fileId);
  const lineItemsPromise = getContractObjectLineItems(projectId, fileId);
  const emphasisPromise = getContractObjectEmphasis(projectId, fileId);
  const verificationPromise = getContractObjectVerification(projectId, fileId);

  // Get project
  const projectPromise = getContractProjectById(projectId);
  const settingsPromise = getContractProjectSettings(projectId);

  const [
    contract,
    lineItems,
    emphasis,
    verification,
    fileRes,
    contractsList,
    project,
    settings,
  ] = await Promise.all([
    contractPromise,
    lineItemsPromise,
    emphasisPromise,
    verificationPromise,
    filePromise,
    contractsListPromise,
    projectPromise,
    settingsPromise,
  ]);

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
        selectedContract={contract}
        contractsList={contractsList}
      />
    </div>
  );
}
