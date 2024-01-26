"use server";
import { redirect } from "next/navigation";
import type { AppInstanceObject, ApplicationObject, Initializers, S3IngestFormDTO, S3PreprocessFormDTO } from "./interfaces";
import { isGetApplicationListReponse, isGetApplicationResponse, isGetInstanceListResponse } from "./discriminators";


const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL;


const APP_REVALIDATION_TIME = 3600; // one hour
const INSTANCE_REVALIDATION_TIME = 60; // one minute



// eslint-disable-next-line @typescript-eslint/require-await -- server actions must be async
export async function logOut(): Promise<void> {
  redirect(`${process.env.NEXTAUTH_URL}/api/signout`);
}


export async function getApplicationList(): Promise<ApplicationObject[]> {
  const url = new URL(`${BACKEND_URL}/application`);
  const response = await fetch(url, { next: { revalidate: APP_REVALIDATION_TIME } });

  if (!response.ok) throw new Error("Failed to fetch");
  const data: unknown = await response.json();
  if (isGetApplicationListReponse(data)) return data;
  throw new Error("Invalid data type");
}


export async function getApplicationById(id: string): Promise<ApplicationObject|undefined> {
  const url = new URL(`${BACKEND_URL}/application/${id}`);
  const response = await fetch(url, { next: { revalidate: APP_REVALIDATION_TIME } });

  if (!response.ok) throw new Error("Failed to fetch");
  const data: unknown = await response.json();
  if (isGetApplicationResponse(data)) return data;
  throw new Error("Invalid data type");
}



export async function getApplicationInstanceList(id: string): Promise<AppInstanceObject[]> {  
  const url = new URL(`${BACKEND_URL}/application/${id}/instance`);
  const response = await fetch(url, { next: { revalidate: INSTANCE_REVALIDATION_TIME } });

  if (!response.ok) throw new Error("Failed to fetch");
  const data: unknown = await response.json();
  if (isGetInstanceListResponse(data)) return data;
  throw new Error("Invalid data type");
}



export async function createApplicationInstance(id: string, dto: Initializers) {
  let url = "";
  // TODO: Make this properly
  if (id === "1") {
    url = "s3";
  } else if (id === "2") {
    url = "";
  } else {
    url = "s3";
  }

  const headers = new Headers();
  headers.append("Content-Type", "application/json");


  const response = await fetch(`${BACKEND_URL}/application/${id}/instance/${url}`, {
    method: "POST",
    body: JSON.stringify(dto),
    headers: headers,
  });
  console.log("Server response:", response);
  if (!response.ok) throw new Error("Failed to upload");
}
