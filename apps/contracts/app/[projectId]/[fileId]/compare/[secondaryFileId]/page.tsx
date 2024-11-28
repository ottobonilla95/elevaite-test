import {
  getContractObjectById, getContractObjectEmphasis, getContractObjectLineItems, getContractObjectVerification,
  getContractProjectById, getContractProjectContracts, getContractProjectSettings,
} from "@repo/contracts-ui/actions";
import { PdfAndExtraction } from "@repo/contracts-ui/components";
import {
  type ContractObject, type ContractObjectEmphasis,
  type ContractObjectVerification, type ContractObjectVerificationLineItem,
  type ContractProjectObject, type ContractSettings,
} from "@repo/contracts-ui/interfaces";
import "../../../page.scss";


interface ComparePageProps {
  readonly params: Promise<{
    projectId: string;
    fileId: string;
    secondaryFileId: string
  }>
}

export default async function ComparePage({ params }: ComparePageProps): Promise<JSX.Element> {
  const { projectId, fileId, secondaryFileId } = await params;

  

  // Get project
  const projectPromise = getContractProjectById(projectId);
  const settingsPromise = getContractProjectSettings(projectId);
  const contractsListPromise = projectId ? getContractProjectContracts(projectId) : Promise.resolve([]);
  // Get primary contract  
  const [primaryContractPromise, primaryLineItemsPromise, primaryEmphasisPromise, primaryVerificationPromise] = getContractPromises(fileId);
  // Get secondary contract
  const [secondaryContractPromise, secondaryLineItemsPromise, secondaryEmphasisPromise, secondaryVerificationPromise] = getContractPromises(secondaryFileId);

  // Await all promises
  const [
    project, settings, contractsList,
    primaryContract, primaryLineItems, primaryEmphasis, primaryVerification,
    secondaryContract, secondaryLineItems, secondaryEmphasis, secondaryVerification,
  ] = await Promise.all([
    projectPromise, settingsPromise, contractsListPromise,
    primaryContractPromise, primaryLineItemsPromise, primaryEmphasisPromise, primaryVerificationPromise,
    secondaryContractPromise, secondaryLineItemsPromise, secondaryEmphasisPromise, secondaryVerificationPromise,
  ]);




  function getContractPromises(id: string): [Promise<ContractObject>, Promise<ContractObjectVerificationLineItem[]>, Promise<ContractObjectEmphasis>, Promise<ContractObjectVerification>,] {
    const contractPromise = getContractObjectById(projectId, id);
    const lineItemsPromise = getContractObjectLineItems(projectId, id);
    const emphasisPromise = getContractObjectEmphasis(projectId, id);
    const verificationPromise = getContractObjectVerification(projectId, id);
    return [contractPromise, lineItemsPromise, emphasisPromise, verificationPromise ];
  }

  function getCombinedProject(projectMain?: ContractProjectObject, projectSettings?: ContractSettings, projectReports?: ContractObject[]): ContractProjectObject|undefined {
    if (!projectMain) return;
    return {
      ...projectMain,
      settings: projectSettings,
      reports: projectReports ?? [],
    };
  }

  function getCombinedContract(contract?: ContractObject, lineItems?: ContractObjectVerificationLineItem[], emphasis?: ContractObjectEmphasis, verification?: ContractObjectVerification): ContractObject|undefined {
    if (!contract) return;
    return {
      ...contract,
      line_items: lineItems ?? [],
      highlight: emphasis,
      verification
    };
  }
  



  return (
    <div className="contracts-main-container">
      <PdfAndExtraction
        projectId={projectId}
        project={getCombinedProject(project, settings, contractsList)}
        contract={getCombinedContract(primaryContract, primaryLineItems, primaryEmphasis, primaryVerification)}
        comparedContract={getCombinedContract(secondaryContract, secondaryLineItems, secondaryEmphasis, secondaryVerification)}
      />
    </div>
  );
}
