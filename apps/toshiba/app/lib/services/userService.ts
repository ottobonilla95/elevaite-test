"use server";

import { revalidatePath } from "next/cache";
import { auth } from "../../../auth";

interface CreateUserParams {
  firstName: string;
  lastName: string;
  email: string;
  password: string;
  isOneTimePassword: boolean;
  isApplicationAdmin: boolean;
}

export async function createUser(
  params: CreateUserParams
): Promise<{ success: boolean; message: string }> {
  try {
    const {
      firstName,
      lastName,
      email,
      password,
      isOneTimePassword,
      isApplicationAdmin,
    } = params;
    const fullName = `${firstName} ${lastName}`.trim();

    const session = await auth();
    const authToken = session?.authToken;

    if (!authToken) {
      return {
        success: false,
        message: "Authentication required. Please log in again.",
      };
    }

    const backendUrl = process.env.NEXT_PUBLIC_AUTH_API_URL;
    const tenantId = process.env.NEXT_PUBLIC_AUTH_TENANT_ID ?? "default";

    if (!backendUrl) {
      return {
        success: false,
        message: "Server configuration error.",
      };
    }

    const apiUrl = backendUrl.replace("localhost", "127.0.0.1");

    console.log("Making request to:", `${apiUrl}/api/auth/admin/create-user`);
    console.log("With headers:", {
      "Content-Type": "application/json",
      "X-Tenant-ID": tenantId,
      Authorization: `Bearer ${authToken ? "***" : "missing"}`,
    });
    console.log("With body:", {
      email,
      full_name: fullName,
      password: "***",
      is_one_time_password: isOneTimePassword,
      application_admin: isApplicationAdmin,
    });

    const response = await fetch(`${apiUrl}/api/auth/admin/create-user`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Tenant-ID": tenantId,
        Authorization: `Bearer ${authToken}`,
      },
      body: JSON.stringify({
        email,
        full_name: fullName,
        password,
        is_one_time_password: isOneTimePassword,
        application_admin: isApplicationAdmin,
      }),
    });

    console.log("Response status:", response.status);
    console.log("Response ok:", response.ok);

    if (!response.ok) {
      const errorText = await response.text();
      console.log("Error response:", errorText);

      let errorMessage = "Failed to create user";

      try {
        const errorData = JSON.parse(errorText);
        errorMessage = errorData.detail || errorData.message || errorMessage;
      } catch {
        if (response.status === 401) {
          errorMessage = "Unauthorized. Please log in again.";
        } else if (response.status === 403) {
          errorMessage = "Forbidden. Admin privileges required.";
        }
      }

      return {
        success: false,
        message: errorMessage,
      };
    }

    const responseData = await response.json();
    console.log("Success response:", responseData);

    revalidatePath("/access");

    return {
      success: true,
      message: `We've sent a user invitation to ${email}. Once they accept the invitation, they will be able to access the system.`,
    };
  } catch (error) {
    console.error("User creation error:", error);
    return {
      success: false,
      message: "An unexpected error occurred.",
    };
  }
}
