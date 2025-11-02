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
  isManager: boolean;
}

export async function createUser(
  params: CreateUserParams
): Promise<{ 
  success: boolean; 
  message: string;
  error?: {
    type?: string;
    message?: string;
    user_id?: number;
    deleted_at?: string;
    suggestion?: string;
  };
}> {
  try {
    const {
      firstName,
      lastName,
      email,
      password,
      isOneTimePassword,
      isApplicationAdmin,
      isManager,
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
        is_manager: isManager,
      }),
    });

    console.log("Response status:", response.status);

    if (!response.ok) {
      const errorText = await response.text();
      console.log("Error response:", errorText);

      let errorMessage = "Failed to create user";

      try {
        const errorData = JSON.parse(errorText);
        
        // Check if it's a structured error (409 with detail object)
        if (response.status === 409 && typeof errorData.detail === 'object' && errorData.detail.type) {
          console.log("Detected deleted user conflict:", errorData.detail);
          return {
            success: false,
            message: errorData.detail.message || "User already exists",
            error: errorData.detail,
          };
        }
        
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

export async function reactivateUser(
  userId: number
): Promise<{ success: boolean; message: string; user?: any }> {
  try {
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

    console.log("Reactivating user:", userId);

    const response = await fetch(
      `${apiUrl}/api/auth/admin/reactivate-user/${userId}`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Tenant-ID": tenantId,
          Authorization: `Bearer ${authToken}`,
        },
      }
    );

    console.log("Reactivate response status:", response.status);

    if (!response.ok) {
      const errorText = await response.text();
      console.log("Reactivate error response:", errorText);

      let errorMessage = "Failed to reactivate user";

      try {
        const errorData = JSON.parse(errorText);
        errorMessage = errorData.detail || errorData.message || errorMessage;
      } catch {
        if (response.status === 401) {
          errorMessage = "Unauthorized. Please log in again.";
        } else if (response.status === 403) {
          errorMessage = "Forbidden. Admin privileges required.";
        } else if (response.status === 404) {
          errorMessage = "User not found.";
        }
      }

      return {
        success: false,
        message: errorMessage,
      };
    }

    const responseData = await response.json();
    console.log("Reactivate success response:", responseData);

    revalidatePath("/access");

    return {
      success: true,
      message: responseData.message || "User reactivated successfully",
      user: responseData.user,
    };
  } catch (error) {
    console.error("User reactivation error:", error);
    return {
      success: false,
      message: "An unexpected error occurred.",
    };
  }
}

export async function deleteUser(
  userId: number
): Promise<{ success: boolean; message: string }> {
  try {
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

    const response = await fetch(`${apiUrl}/api/auth/admin/delete-user/${userId}`, {
      method: "DELETE",
      headers: {
        "Content-Type": "application/json",
        "X-Tenant-ID": tenantId,
        Authorization: `Bearer ${authToken}`,
      },
    });

    if (!response.ok) {
      const errorText = await response.text();
      let errorMessage = "Failed to delete user";

      try {
        const errorData = JSON.parse(errorText);
        errorMessage = errorData.detail || errorData.message || errorMessage;
      } catch {
        if (response.status === 401) {
          errorMessage = "Unauthorized. Please log in again.";
        } else if (response.status === 403) {
          errorMessage = "Forbidden. Admin privileges required.";
        } else if (response.status === 404) {
          errorMessage = "User not found.";
        }
      }

      return {
        success: false,
        message: errorMessage,
      };
    }

    const responseData = await response.json();
    revalidatePath("/access");

    return {
      success: true,
      message: responseData.message || "User deleted successfully.",
    };
  } catch (error) {
    console.error("User deletion error:", error);
    return {
      success: false,
      message: "An unexpected error occurred.",
    };
  }
}

export async function updateUserRoles(
  userId: number,
  roles: { application_admin?: boolean; is_manager?: boolean }
): Promise<{ success: boolean; message: string }> {
  try {
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

    const response = await fetch(`${apiUrl}/api/auth/admin/update-user/${userId}`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        "X-Tenant-ID": tenantId,
        Authorization: `Bearer ${authToken}`,
      },
      body: JSON.stringify(roles),
    });

    if (!response.ok) {
      const errorText = await response.text();
      let errorMessage = "Failed to update user roles";

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
    revalidatePath("/access");

    return {
      success: true,
      message: responseData.message || "User roles updated successfully.",
    };
  } catch (error) {
    console.error("User role update error:", error);
    return {
      success: false,
      message: "An unexpected error occurred.",
    };
  }
}
export async function toggleBiometricMFA(
  enabled: boolean
): Promise<{ success: boolean; message: string }> {
  try {
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

    const response = await fetch(`${apiUrl}/api/biometric/toggle-setting`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Tenant-ID": tenantId,
        Authorization: `Bearer ${authToken}`,
      },
      body: JSON.stringify({ enabled }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      let errorMessage = "Failed to update biometric setting";

      try {
        const errorData = JSON.parse(errorText);
        errorMessage = errorData.detail || errorData.message || errorMessage;
      } catch {
        if (response.status === 401) {
          errorMessage = "Unauthorized. Please log in again.";
        } else if (response.status === 403) {
          errorMessage = "Forbidden. Insufficient privileges.";
        }
      }

      return {
        success: false,
        message: errorMessage,
      };
    }

    const responseData = await response.json();

    return {
      success: true,
      message: responseData.message || `Biometric MFA ${enabled ? "enabled" : "disabled"} successfully.`,
    };
  } catch (error) {
    console.error("Toggle biometric MFA error:", error);
    return {
      success: false,
      message: "An unexpected error occurred.",
    };
  }
}