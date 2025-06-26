"use server";

import { revalidatePath } from "next/cache";
import { auth } from "../../../auth";

interface CreateUserParams {
  firstName: string;
  lastName: string;
  email: string;
  password: string;
  isOneTimePassword: boolean;
}

export async function createUser(
  params: CreateUserParams
): Promise<{ success: boolean; message: string }> {
  try {
    const { firstName, lastName, email, password, isOneTimePassword } = params;
    const fullName = `${firstName} ${lastName}`.trim();

    const session = await auth();
    const authToken = session?.authToken;

    if (!authToken) {
      return {
        success: false,
        message: "Authentication required. Please log in again.",
      };
    }

    const backendUrl = process.env.AUTH_API_URL;
    const tenantId = process.env.AUTH_TENANT_ID ?? "default";

    if (!backendUrl) {
      return {
        success: false,
        message: "Server configuration error.",
      };
    }

    // Fix localhost IPv6 issue by using 127.0.0.1
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
      message: "User created successfully.",
    };
  } catch (error) {
    console.error("User creation error:", error);
    return {
      success: false,
      message: "An unexpected error occurred.",
    };
  }
}
