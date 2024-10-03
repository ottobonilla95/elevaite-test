"use server";
import { revalidateTag } from "next/cache";
import { type CONTRACT_TYPES, type ContractExtractionDictionary } from "../interfaces";
import { cacheTags } from "./actionConstants";
import { isSubmitContractResponse } from "./contractDiscriminators";



const CONTRACTS_URL = process.env.NEXT_PUBLIC_CONTRACTS_API_URL;




// GETS
//////////////////








// POSTS
//////////////////

export async function submitContract(formData: FormData, type: CONTRACT_TYPES): Promise<ContractExtractionDictionary> {
    if (!CONTRACTS_URL) throw new Error("Missing base url");
  
    const url = new URL(`${CONTRACTS_URL}/files/`);
    url.searchParams.set("content_type", type);

    const response = await fetch(url, {
      method: "POST",
      body: formData,
    });

    revalidateTag(cacheTags.contracts);
    if (!response.ok) {
      // if (response.status === 422) {
        const errorData: unknown = await response.json();
        // eslint-disable-next-line no-console -- Need this in case this breaks like that.
        console.dir(errorData, { depth: null });
      // }
      throw new Error("Failed to submit contract");
    }
    const data: unknown = await response.json();
    if (isSubmitContractResponse(data)) return data;
    throw new Error("Invalid data type");
  }

