import { getContractObjectById, getContractObjectVerification, getContractProjectById } from "@repo/contracts-ui/actions";
import { PdfAndExtraction } from "@repo/contracts-ui/components";
import "../page.scss";


interface ContractPageProps {
  readonly params: Promise<{
    projectId: string;
    fileId: string;
  }>
}

export default async function ContractPage({params}: ContractPageProps): Promise<JSX.Element> {
  const { projectId, fileId } = await params;


  // Get file
  let filePromise: Promise<Response>|undefined;
  const CONTRACTS_URL = process.env.NEXT_PUBLIC_CONTRACTS_API_URL;
  if (CONTRACTS_URL) {
    const url = new URL(`${CONTRACTS_URL}/projects/${projectId}/files/${fileId}/file`);
    filePromise = fetch(url, { method: "GET" });
  }
  // Get project
  const projectPromise = getContractProjectById(projectId);
  // Get contracts
  const contractPromise = getContractObjectById(projectId, fileId);
  const verificationPromise = getContractObjectVerification(projectId, fileId);


  const [contract, verification, fileRes, project, ] = 
    await Promise.all([ contractPromise, verificationPromise, filePromise, projectPromise, ]);

  const file = fileRes ? await fileRes.blob() : undefined;

  return (
    <div className="contracts-main-container">
      <PdfAndExtraction
        file={file}
        projectId={projectId}
        project={project}
        contract={{...contract, verification}}
      />
    </div>
  );
}
