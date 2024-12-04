import { getContractObjectById, getContractObjectEmphasis, getContractObjectLineItems, getContractObjectVerification, getContractProjectById, getContractProjectContracts, getContractProjectSettings } from "@repo/contracts-ui/actions";
import { PdfAndExtraction } from "@repo/contracts-ui/components";
import { type ContractObject, type ContractObjectEmphasis, type ContractObjectVerification, type ContractObjectVerificationLineItem, type ContractProjectObject, type ContractSettings } from "@repo/contracts-ui/interfaces";
import "../../page.scss";

interface ComparePageSingleProps {
  readonly params: Promise<{
    projectId: string;
    fileId: string;
  }>
}


export default async function ComparePageSingle({ params }: ComparePageSingleProps): Promise<JSX.Element> {
  const { projectId, fileId } = await params;

  

  // Get project
  const projectPromise = getContractProjectById(projectId);
  const settingsPromise = getContractProjectSettings(projectId);
  const contractsListPromise = projectId ? getContractProjectContracts(projectId) : Promise.resolve([]);
  // Get primary contract 
  const contractPromise = getContractObjectById(projectId, fileId);
  const lineItemsPromise = getContractObjectLineItems(projectId, fileId);
  const emphasisPromise = getContractObjectEmphasis(projectId, fileId);
  const verificationPromise = getContractObjectVerification(projectId, fileId);

  // Await all promises
  const [
    project, settings, contractsList,
    primaryContract, primaryLineItems, primaryEmphasis, primaryVerification,
  ] = await Promise.all([
    projectPromise, settingsPromise, contractsListPromise,
    contractPromise, lineItemsPromise, emphasisPromise, verificationPromise,
  ]);



  

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
        comparedContract
      />
    </div>
  );
}
