import { getContractObjectById, getContractObjectVerification, getContractProjectById } from "@repo/contracts-ui/actions";
import { PdfAndExtraction } from "@repo/contracts-ui/components";
import { type ContractObject, type ContractObjectVerification, type ContractProjectObject } from "@repo/contracts-ui/interfaces";
import { redirect } from "next/navigation";
import "../page.scss";


interface ContractPageProps {
  readonly params: Promise<{
    projectId: string;
    fileId: string;
  }>
}

export default async function ContractPage({params}: ContractPageProps): Promise<JSX.Element> {
  const { projectId, fileId } = await params;
  let contract: ContractObject|undefined;
  let verification: ContractObjectVerification|undefined;
  let fileRes: Response|undefined;
  let project: ContractProjectObject|undefined;
  

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


  try {
    [contract, verification, fileRes, project, ] = await Promise.all([ contractPromise, verificationPromise, filePromise, projectPromise, ]);
  } catch (error) { redirect("/"); }

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
