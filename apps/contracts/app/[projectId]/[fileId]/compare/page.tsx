import { redirect } from "next/navigation";

export default async function ContractPage({
  params,
}: Readonly<{
  params: Promise<{
    projectId: string;
    fileId: string;
  }>;
}>) {
  const { projectId, fileId } = await params;
  redirect(`/${projectId}/${fileId}/compare/0`);
}
