"use server";
import { AuthError } from "next-auth";
import { signIn, signOut, auth } from "../../../auth"; import {
  isChatMessageResponse,
  isSessionSummaryResponse,
} from "./discriminators";
import type {
  ChatBotGenAI,
  ChatMessageResponse,
  ChatbotV,
  SessionSummaryObject,
} from "./interfaces";
import {
  type SummaryMetrics,
  type TrendData,
  type DistributionData,
  type SeverityData,
  type CustomerData,
  type PartsData,
  type MachineOverviewData,
  type MachineDetail,
  type IssueConcentration,
  type CustomerHeatmapData,
  type CustomerProportion,
  type CustomerRequestData,
  type CategoryBarData,
  type CustomerTypeIssue,
  type IssueCategoryData,
  type IssueStatistics,
  type MachineTypeIssue,
  type RegionTravelTime,
  type ServiceMetrics,
  type TechnicianPerformance,
  type TimeAnalysis,
  type PartsIssueCorrelation,
  type ReplacedPartsOverview,
  type MachinePartsBreakdown,
} from "./types";
import { buildAbsoluteUrl } from "./urlUtils";

// Example: NEXT_PUBLIC_BACKEND_URL=https://tgcs.iopex.ai/api/core/
// Example: NEXT_PUBLIC_API_URL=https://tgcs.iopex.ai
const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL;
const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

interface DateFilters {
  start_date?: string;
  end_date?: string;
  manager_id?: number | null;
  fst_id?: number | null;
  product_type?: string;
}

export async function authenticate(
  _prevState: string | undefined,
  formData: Record<"email" | "password", string> & { totp_code?: string }
): Promise<
  | "Invalid credentials."
  | "Email not verified."
  | "Admin access required."
  | "Something went wrong."
  | "MFA_REQUIRED_TOTP"
  | "MFA_REQUIRED_SMS"
  | "MFA_REQUIRED_EMAIL"
  | "MFA_REQUIRED_MULTIPLE"
  | { type: "MFA_ERROR"; error: unknown }
  | undefined
> {
  try {
    await signIn("credentials", formData);
    return undefined;
  } catch (error) {
    if (error instanceof AuthError) {
      if (error.cause instanceof Error) {
        if (error.cause.message === "MFA_REQUIRED_TOTP") {
          return {
            type: "MFA_ERROR",
            error: {
              message: error.cause.message,
              availableMethods: (error.cause as any).availableMethods,
              maskedPhone: (error.cause as any).maskedPhone,
              maskedEmail: (error.cause as any).maskedEmail,
            },
          };
        }
        if (error.cause.message === "MFA_REQUIRED_SMS") {
          return {
            type: "MFA_ERROR",
            error: {
              message: error.cause.message,
              availableMethods: (error.cause as any).availableMethods,
              maskedPhone: (error.cause as any).maskedPhone,
              maskedEmail: (error.cause as any).maskedEmail,
            },
          };
        }
        if (error.cause.message === "MFA_REQUIRED_EMAIL") {
          return {
            type: "MFA_ERROR",
            error: {
              message: error.cause.message,
              availableMethods: (error.cause as any).availableMethods,
              maskedPhone: (error.cause as any).maskedPhone,
              maskedEmail: (error.cause as any).maskedEmail,
            },
          };
        }
        if (error.cause.message === "MFA_REQUIRED_MULTIPLE") {
          return {
            type: "MFA_ERROR",
            error: {
              message: error.cause.message,
              availableMethods: (error.cause as any).availableMethods,
              maskedPhone: (error.cause as any).maskedPhone,
              maskedEmail: (error.cause as any).maskedEmail,
            },
          };
        }
      }
      switch (error.type) {
        case "CredentialsSignin":
          return "Invalid credentials.";
        case "CallbackRouteError":
          if (
            error.cause &&
            typeof error.cause === "object" &&
            "err" in error.cause
          ) {
            const causeError = error.cause.err;
            if (causeError instanceof Error) {
              if (causeError.message === "MFA_REQUIRED_TOTP") {
                return {
                  type: "MFA_ERROR",
                  error: {
                    message: causeError.message,
                    availableMethods: (causeError as any).availableMethods,
                    maskedPhone: (causeError as any).maskedPhone,
                    maskedEmail: (causeError as any).maskedEmail,
                  },
                };
              }
              if (causeError.message === "MFA_REQUIRED_SMS") {
                return {
                  type: "MFA_ERROR",
                  error: {
                    message: causeError.message,
                    availableMethods: (causeError as any).availableMethods,
                    maskedPhone: (causeError as any).maskedPhone,
                    maskedEmail: (causeError as any).maskedEmail,
                  },
                };
              }
              if (causeError.message === "MFA_REQUIRED_EMAIL") {
                return {
                  type: "MFA_ERROR",
                  error: {
                    message: causeError.message,
                    availableMethods: (causeError as any).availableMethods,
                    maskedPhone: (causeError as any).maskedPhone,
                    maskedEmail: (causeError as any).maskedEmail,
                  },
                };
              }
              if (causeError.message === "MFA_REQUIRED_MULTIPLE") {
                return {
                  type: "MFA_ERROR",
                  error: {
                    message: causeError.message,
                    availableMethods: (causeError as any).availableMethods,
                    maskedPhone: (causeError as any).maskedPhone,
                    maskedEmail: (causeError as any).maskedEmail,
                  },
                };
              }
            }
          }
          if (error.message.includes("email_not_verified")) {
            return "Email not verified.";
          }
          return "Invalid credentials.";
        default:
          if (error.message.includes("email_not_verified")) {
            return "Email not verified.";
          }
          if (error.message.includes("admin_access_required")) {
            return "Admin access required.";
          }
          return "Something went wrong.";
      }
    }

    if (error instanceof Error) {
      if (error.message === "email_not_verified") {
        return "Email not verified.";
      }
      if (error.message === "MFA_REQUIRED_TOTP") {
        return "MFA_REQUIRED_TOTP";
      }
      if (error.message === "MFA_REQUIRED_SMS") {
        return "MFA_REQUIRED_SMS";
      }
      if (error.message === "MFA_REQUIRED_EMAIL") {
        return "MFA_REQUIRED_EMAIL";
      }
    }

    throw error;
  }
}

export async function fetchQueryWeeklyTrends(
  filters?: DateFilters
): Promise<TrendData[]> {
  try {
    const queryString = buildQueryString(filters);
    const url = `${API_URL}/api/analytics/query-analytics/weekly-trends${queryString}`;

    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`Failed to fetch weekly trends: ${response.status}`);
    }

    const result = await response.json();

    if (Array.isArray(result)) {
      return result;
    } else if (result.data && Array.isArray(result.data)) {
      return result.data;
    }

    return [];
  } catch (error) {
    console.error("Error fetching weekly query trends:", error);
    return [];
  }
}

export async function fetchQueryMonthlyTrends(
  filters?: DateFilters
): Promise<TrendData[]> {
  try {
    const queryString = buildQueryString(filters);
    const url = `${API_URL}/api/analytics/query-analytics/monthly-trends${queryString}`;

    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`Failed to fetch monthly trends: ${response.status}`);
    }

    const result = await response.json();

    if (Array.isArray(result)) {
      return result;
    } else if (result.data && Array.isArray(result.data)) {
      return result.data;
    }

    return [];
  } catch (error) {
    console.error("Error fetching monthly query trends:", error);
    return [];
  }
}

export async function fetchQueryDailyTrends(
  filters?: DateFilters
): Promise<TrendData[]> {
  try {
    const queryString = buildQueryString(filters);
    const url = `${API_URL}/api/analytics/query-analytics/daily-trends${queryString}`;

    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`Failed to fetch daily trends: ${response.status}`);
    }

    const result = await response.json();

    if (Array.isArray(result)) {
      return result;
    } else if (result.data && Array.isArray(result.data)) {
      return result.data;
    }

    return [];
  } catch (error) {
    console.error("Error fetching daily query trends:", error);
    return [];
  }
}

export async function logout(): Promise<void> {
  try {
    const session = await auth();
    const accessToken = session?.authToken ?? session?.user?.accessToken;

    if (accessToken) {
      const authApiUrl = process.env.NEXT_PUBLIC_AUTH_API_URL;
      if (authApiUrl) {
        try {
          const apiUrl = authApiUrl.replace("localhost", "127.0.0.1");
          const tenantId = process.env.NEXT_PUBLIC_AUTH_TENANT_ID ?? "default";

          const refreshToken = session?.user?.refreshToken;

          if (refreshToken) {
            await fetch(`${apiUrl}/api/auth/logout`, {
              method: "POST",
              headers: {
                "Content-Type": "application/json",
                Authorization: `Bearer ${accessToken}`,
                "X-Tenant-ID": tenantId,
              },
              body: JSON.stringify({
                refresh_token: refreshToken,
              }),
            });
          }
        } catch (apiError) {
          // Continue with NextAuth signOut even if API call fails
        }
      }
    }
  } catch (error) {
    // Continue with NextAuth signOut even if preparation fails
  }

  // Use absolute URL for redirect to prevent hostname issues
  const loginUrl = buildAbsoluteUrl("/login");
  await signOut({ redirectTo: loginUrl });
}
export async function resetPassword(newPassword: string): Promise<{
  success: boolean;
  message: string;
  needsPasswordReset?: boolean;
}> {
  console.log(
    "Server Action - resetPassword called with password length:",
    newPassword.length
  );

  try {
    const session = await auth();
    console.log("Server Action - Session:", session?.user?.email);
    console.log(
      "Server Action - Full session:",
      JSON.stringify(session, null, 2)
    );

    const accessToken =
      session?.authToken ??
      session?.user?.accessToken ??
      (session as { accessToken?: string })?.accessToken;

    if (!accessToken) {
      console.error("Server Action - No auth token found in session");
      console.error(
        "Server Action - Session keys:",
        Object.keys(session ?? {})
      );
      if (session?.user) {
        console.error("Server Action - User keys:", Object.keys(session.user));
      }
      throw new Error("No auth token found in session");
    }

    const authApiUrl = process.env.AUTH_API_URL;
    if (!authApiUrl) {
      console.error(
        "Server Action - AUTH_API_URL not found in environment variables"
      );
      throw new Error("AUTH_API_URL not found in environment variables");
    }

    const tenantId = process.env.AUTH_TENANT_ID ?? "default";

    console.log(
      "Server Action - Resetting password for user:",
      session?.user?.email ?? "unknown"
    );
    console.log("Server Action - Using auth API URL:", authApiUrl);
    console.log("Server Action - Using tenant ID:", tenantId);

    const apiUrl = authApiUrl.replace("localhost", "127.0.0.1");

    const response = await fetch(`${apiUrl}/api/auth/change-password`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${accessToken}`,
        "X-Tenant-ID": tenantId,
      },
      body: JSON.stringify({
        new_password: newPassword,
      }),
    });

    // Debug logging
    console.log(
      "Server Action - Password reset response status:",
      response.status
    );

    if (!response.ok) {
      const errorData: unknown = await response.json();
      console.error("Server Action - Password reset error:", errorData);
      return {
        success: false,
        message:
          typeof errorData === "object" &&
            errorData !== null &&
            "detail" in errorData
            ? typeof errorData === "object" && "detail" in errorData
              ? String(errorData.detail)
              : "Unknown error"
            : "Failed to reset password",
      };
    }

    const responseData = await response.json();
    console.log("Server Action - Password reset successful:", responseData);

    return {
      success: true,
      message: "Password successfully changed",
      needsPasswordReset: false,
    };
  } catch (error) {
    console.error("Server Action - Error resetting password:", error);
    return {
      success: false,
      message:
        error instanceof Error ? error.message : "Failed to reset password",
    };
  }
}

export async function fetchEnhancedSummaryMetrics(
  filters?: DateFilters
): Promise<
  SummaryMetrics & {
    total_queries: number;
    avg_queries_per_day: number;
    query_trends: TrendData[];
  }
> {
  try {
    const queryString = buildQueryString(filters);

    const srResponse = await fetch(
      `${API_URL}/api/analytics/summary/metrics${queryString}`
    );
    if (!srResponse.ok) throw new Error("Failed to fetch SR metrics");
    const srData = (await srResponse.json()) as SummaryMetrics;

    let queryData = {
      total_queries: 0,
      avg_queries_per_day: 0,
      query_trends: [] as TrendData[],
    };

    try {
      console.log("🔍 Fetching real query data from chatbot API...");
      const queryResponse = await fetch(
        `${API_URL}/api/analytics/query-analytics/metrics${queryString}`
      );

      if (queryResponse.ok) {
        const realQueryData = await queryResponse.json();
        console.log("✅ Got real query data:", realQueryData);

        queryData = {
          total_queries: realQueryData.total_queries || 0,
          avg_queries_per_day: realQueryData.avg_queries_per_day || 0,
          query_trends: [],
        };

        try {
          const trendsResponse = await fetch(
            `${API_URL}/api/analytics/query-analytics/hourly-usage${queryString}`
          );
          if (trendsResponse.ok) {
            const hourlyData = await trendsResponse.json();
            queryData.query_trends = hourlyData
              .slice(0, 10)
              .map((item: any, index: number) => ({
                date: `Hour ${item.hour}`,
                value: item.queries,
              }));
          }
        } catch (trendsError) {
          console.log("Query trends fetch failed, using empty array");
        }
      } else {
        console.log("Query API returned error:", queryResponse.status);
        queryData = {
          total_queries: 30200,
          avg_queries_per_day: 1007,
          query_trends: [
            { date: "2024-01", value: 4500 },
            { date: "2024-02", value: 5200 },
            { date: "2024-03", value: 6100 },
            { date: "2024-04", value: 5800 },
            { date: "2024-05", value: 6500 },
            { date: "2024-06", value: 7200 },
          ],
        };
      }
    } catch (queryError) {
      console.error("Query API error:", queryError);
      queryData = {
        total_queries: 30200,
        avg_queries_per_day: 1007,
        query_trends: [
          { date: "2024-01", value: 4500 },
          { date: "2024-02", value: 5200 },
          { date: "2024-03", value: 6100 },
          { date: "2024-04", value: 5800 },
          { date: "2024-05", value: 6500 },
          { date: "2024-06", value: 7200 },
        ],
      };
    }

    const enhancedData = {
      ...srData,
      ...queryData,
    };

    console.log("✅ Enhanced summary metrics:", enhancedData);
    return enhancedData;
  } catch (error) {
    console.error("Error fetching enhanced summary metrics:", error);
    throw error;
  }
}

export async function fetchQueryDateRangeInfo(filters?: DateFilters): Promise<{
  available_range: {
    start_date: string | null;
    end_date: string | null;
    total_records: number;
  };
  filtered_range: {
    start_date: string | null;
    end_date: string | null;
    total_records: number;
  };
  requested_range: { start_date: string | null; end_date: string | null };
  has_data_in_range: boolean;
  message: string;
}> {
  try {
    const queryString = buildQueryString(filters);
    const url = `${API_URL}/api/analytics/query-analytics/date-range-info${queryString}`;

    console.log("🔍 Fetching query date range info from:", url);

    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(
        `Failed to fetch query date range info: ${response.status} ${response.statusText}`
      );
    }

    const data = await response.json();
    console.log("✅ Query date range info response:", data);

    return data;
  } catch (error) {
    console.error("❌ Error fetching query date range info:", error);
    // Return fallback data
    return {
      available_range: { start_date: null, end_date: null, total_records: 0 },
      filtered_range: { start_date: null, end_date: null, total_records: 0 },
      requested_range: {
        start_date: filters?.start_date ?? null,
        end_date: filters?.end_date ?? null,
      },
      has_data_in_range: false,
      message: "Unable to load query data information",
    };
  }
}

export async function fetchQueryAnalyticsMetricsEnhanced(
  filters?: DateFilters
): Promise<{
  total_sessions: number;
  total_queries: number;
  total_unique_users: number;
  queries_per_session: number;
  repeat_queries_percentage: number;
  accuracy_percentage: number;
  voter_satisfaction_rate: number;
  engagement_rate: number;
  avg_response_time_seconds: number;
  avg_queries_per_day: number;
  avg_unique_users_per_day: number;
  thumbs_up_percentage: number;
  thumbs_down_percentage: number;
  no_vote_percentage: number;
  feedback_distribution: {
    type: string;
    count: number;
    percentage: number;
  }[];
  _source: string;
  _calculation_method?: string;
  _manager_filter_applied?: boolean;
  _fst_filter_applied?: boolean;
  _debug?: {
    total_voted: number;
    thumbs_up_count: number;
    thumbs_down_count: number;
    sessions_with_repeats: number;
    total_sessions_analyzed: number;
  };
}> {
  try {
    const queryString = buildQueryString(filters);
    const url = `${API_URL}/api/analytics/query-analytics/metrics${queryString}`;

    console.log("Fetching REAL query analytics metrics from:", url);

    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(
        `Failed to fetch query analytics metrics: ${response.status} ${response.statusText}`
      );
    }

    const data = await response.json();
    console.log("REAL query analytics metrics response:", data);

    return data;
  } catch (error) {
    console.error("Error fetching REAL query analytics metrics:", error);
    return {
      total_sessions: 0,
      total_queries: 0,
      total_unique_users: 0,
      queries_per_session: 0,
      repeat_queries_percentage: 0,
      accuracy_percentage: 0,
      voter_satisfaction_rate: 0,
      engagement_rate: 0,
      avg_response_time_seconds: 0,
      avg_queries_per_day: 0,
      avg_unique_users_per_day: 0,
      thumbs_up_percentage: 0,
      thumbs_down_percentage: 0,
      no_vote_percentage: 0,
      feedback_distribution: [],
      _source: "error_no_data",
    };
  }
}
export async function fetchQueryAnalyticsHourlyUsageEnhanced(
  filters?: DateFilters
): Promise<
  Array<{
    hour: string;
    queries: number;
  }>
> {
  try {
    const queryString = buildQueryString(filters);
    const url = `${API_URL}/api/analytics/query-analytics/hourly-usage${queryString}`;

    console.log("🔍 Fetching REAL query analytics hourly usage from:", url);

    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(
        `Failed to fetch query analytics hourly usage: ${response.status} ${response.statusText}`
      );
    }

    const data = await response.json();
    console.log(
      "✅ REAL query analytics hourly usage response:",
      data.length,
      "data points"
    );

    return data;
  } catch (error) {
    console.error(
      "❌ Error fetching REAL query analytics hourly usage:",
      error
    );
    // Return empty 24-hour data instead of random fallback
    return Array.from({ length: 24 }, (_, hour) => ({
      hour: `${hour.toString().padStart(2, "0")}:00`,
      queries: 0,
    }));
  }
}

export async function fetchQueryAnalyticsUnresolvedQueriesEnhanced(
  filters?: DateFilters,
  limit = 20
): Promise<
  {
    text: string;
    count: number;
    percentage: string;
    feedback: string;
    botConfidence: string;
    thumbs_down_count: number;
    thumbs_up_count: number;
  }[]
> {
  try {
    const params = new URLSearchParams();
    if (filters?.start_date) params.append("start_date", filters.start_date);
    if (filters?.end_date) params.append("end_date", filters.end_date);
    params.append("limit", limit.toString());

    const queryString = `?${params.toString()}`;
    const url = `${API_URL}/api/analytics/query-analytics/unresolved-queries${queryString}`;

    console.log("🔍 Fetching REAL unresolved queries from:", url);

    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(
        `Failed to fetch unresolved queries: ${response.status} ${response.statusText}`
      );
    }

    const data = await response.json();
    console.log("✅ REAL unresolved queries response:", data.length, "queries");

    return data;
  } catch (error) {
    console.error("❌ Error fetching REAL unresolved queries:", error);
    return [];
  }
}

export async function fetchQueryAnalyticsFeedbackQueriesEnhanced(
  feedbackType: "thumbs_up" | "thumbs_down",
  filters?: DateFilters,
  limit = 50
): Promise<
  {
    query: string;
    response: string;
    timestamp: string;
    user: string;
    feedback: string;
    session_id: string;
  }[]
> {
  try {
    const params = new URLSearchParams();
    if (filters?.start_date) params.append("start_date", filters.start_date);
    if (filters?.end_date) params.append("end_date", filters.end_date);
    params.append("feedback_type", feedbackType);
    params.append("limit", limit.toString());

    const queryString = `?${params.toString()}`;
    const url = `${API_URL}/api/analytics/query-analytics/feedback-queries${queryString}`;

    console.log(" Fetching REAL query analytics feedback queries from:", url);

    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(
        `Failed to fetch query analytics feedback queries: ${response.status} ${response.statusText}`
      );
    }

    const data = await response.json();
    console.log(
      " REAL query analytics feedback queries response:",
      data.length,
      "queries"
    );

    return data;
  } catch (error) {
    console.error(
      " Error fetching REAL query analytics feedback queries:",
      error
    );
    return [];
  }
}

export async function testQueryAnalyticsConnectionEnhanced(): Promise<{
  status: string;
  message: string;
  total_queries?: number;
}> {
  try {
    const url = `${API_URL}/api/analytics/query-analytics/test-connection`;

    console.log(" Testing REAL query analytics connection:", url);

    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(
        `Failed to test query analytics connection: ${response.status} ${response.statusText}`
      );
    }

    const data = await response.json();
    console.log(" REAL query analytics connection test response:", data);

    return data;
  } catch (error) {
    console.error(" Error testing REAL query analytics connection:", error);
    return {
      status: "error",
      message:
        error instanceof Error ? error.message : "Connection test failed",
    };
  }
}

// ============ EXCEL EXPORT FUNCTIONS - REAL DATA ONLY ============

export async function exportQueryAnalyticsToExcel(
  exportType:
    | "all-queries"
    | "thumbs-up"
    | "thumbs-down"
    | "no-feedback"
    | "queries-with-fst-feedback",
  filters?: DateFilters
): Promise<{ success: boolean; message?: string; error?: string }> {
  try {
    console.log(`Starting real data export: ${exportType}`);

    const params = new URLSearchParams();
    if (filters?.start_date) params.append("start_date", filters.start_date);
    if (filters?.end_date) params.append("end_date", filters.end_date);

    const queryString = params.toString() ? `?${params.toString()}` : "";

    // 2. UPDATE the endpointMap to include 'no-feedback'
    const endpointMap = {
      "all-queries": "/export/all-queries",
      "thumbs-up": "/export/thumbs-up",
      "thumbs-down": "/export/thumbs-down",
      "no-feedback": "/export/no-feedback", // ADD THIS LINE
      "queries-with-fst-feedback": "/export/queries-with-fst-feedback",
    };

    const endpoint = endpointMap[exportType];
    const url = `${API_URL}/api/analytics/query-analytics${endpoint}${queryString}`;

    console.log(`Checking export response: ${url}`);

    const response = await fetch(url);
    const contentType = response.headers.get("Content-Type") || "";

    if (contentType.includes("application/json")) {
      const errorData = await response.json();
      if (errorData.error === "date_range_required") {
        return {
          success: false,
          error: "date_range_required",
          message:
            errorData.message ?? "Please select a date range to export data.",
        };
      }
      return {
        success: false,
        message: errorData.message ?? "Export failed",
      };
    } else if (
      contentType.includes("spreadsheet") ||
      contentType.includes("excel")
    ) {
      console.log(`Real data export successful: ${exportType}`);
      return { success: true };
    }
    return {
      success: false,
      message: "Unexpected response format from export API",
    };
  } catch (error) {
    console.error(`Export failed:`, error);
    return {
      success: false,
      message: `Export failed: ${error instanceof Error ? error.message : "Unknown error"}`,
    };
  }
}

export async function fetchTopUsersFromUserAnalytics(
  filters?: DateFilters,
  limit = 10
): Promise<
  {
    user_id: string;
    total_queries: number;
    total_sessions: number;
    last_active: string;
    avg_queries_per_session: number;
    satisfaction_rate: number;
    thumbs_up_count: number;
    thumbs_down_count: number;
    days_active: number;
  }[]
> {
  try {
    const params = new URLSearchParams();
    if (filters?.start_date) params.append("start_date", filters.start_date);
    if (filters?.end_date) params.append("end_date", filters.end_date);
    params.append("limit", limit.toString());

    const queryString = `?${params.toString()}`;
    const url = `${API_URL}/api/analytics/user-analytics/top-users${queryString}`;

    console.log("Fetching top users from user analytics:", url);

    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(
        `Failed to fetch top users: ${response.status} ${response.statusText}`
      );
    }

    const data = await response.json();
    console.log("Top users response:", data.length, "users");

    return data;
  } catch (error) {
    console.error("Error fetching top users from user analytics:", error);
    return [];
  }
}

export async function fetchUserBreakdownFromUserAnalytics(
  filters?: DateFilters,
  page = 1,
  pageSize = 50
): Promise<
  {
    user_id: string;
    total_queries: number;
    total_sessions: number;
    first_query: string;
    last_active: string;
    avg_queries_per_day: number;
    satisfaction_rate: number;
    most_active_hour: number;
    repeat_query_rate: number;
  }[]
> {
  try {
    const params = new URLSearchParams();
    if (filters?.start_date) params.append("start_date", filters.start_date);
    if (filters?.end_date) params.append("end_date", filters.end_date);
    params.append("page", page.toString());
    params.append("page_size", pageSize.toString());

    const queryString = `?${params.toString()}`;
    const url = `${API_URL}/api/analytics/user-analytics/user-breakdown${queryString}`;

    console.log("Fetching user breakdown from user analytics:", url);

    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(
        `Failed to fetch user breakdown: ${response.status} ${response.statusText}`
      );
    }

    const data = await response.json();
    console.log("User breakdown response:", data.length, "users");

    return data;
  } catch (error) {
    console.error("Error fetching user breakdown from user analytics:", error);
    return [];
  }
}

export async function fetchUserMetricsFromUserAnalytics(
  filters?: DateFilters
): Promise<{
  total_unique_users: number;
  avg_queries_per_user: number;
  avg_sessions_per_user: number;
  most_active_user: string;
  newest_user: string;
  user_growth_rate: number;
}> {
  try {
    const params = new URLSearchParams();
    if (filters?.start_date) params.append("start_date", filters.start_date);
    if (filters?.end_date) params.append("end_date", filters.end_date);

    const queryString = params.toString() ? `?${params.toString()}` : "";
    const url = `${API_URL}/api/analytics/user-analytics/user-metrics${queryString}`;

    console.log("Fetching user metrics from user analytics:", url);

    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(
        `Failed to fetch user metrics: ${response.status} ${response.statusText}`
      );
    }

    const data = await response.json();
    console.log("User metrics response:", data);

    return data;
  } catch (error) {
    console.error("Error fetching user metrics from user analytics:", error);
    return {
      total_unique_users: 0,
      avg_queries_per_user: 0,
      avg_sessions_per_user: 0,
      most_active_user: "",
      newest_user: "",
      user_growth_rate: 0,
    };
  }
}

export async function fetchDailyUniqueUsersFromUserAnalytics(
  filters?: DateFilters
): Promise<
  {
    date: string;
    value: number;
  }[]
> {
  try {
    const params = new URLSearchParams();
    if (filters?.start_date) params.append("start_date", filters.start_date);
    if (filters?.end_date) params.append("end_date", filters.end_date);

    const queryString = params.toString() ? `?${params.toString()}` : "";
    const url = `${API_URL}/api/analytics/user-analytics/daily-unique-users${queryString}`;

    console.log("Fetching daily unique users from user analytics:", url);

    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(
        `Failed to fetch daily unique users: ${response.status} ${response.statusText}`
      );
    }

    const data = await response.json();
    console.log("Daily unique users response:", data.length, "data points");

    return data;
  } catch (error) {
    console.error(
      "Error fetching daily unique users from user analytics:",
      error
    );
    return [];
  }
}

export async function exportUserAnalyticsToExcelFromUserAnalytics(
  filters?: DateFilters,
  userId?: string
): Promise<{ success: boolean; message?: string; error?: string }> {
  try {
    console.log(
      `Starting user analytics export${userId ? ` for user: ${userId}` : ""}`
    );

    const params = new URLSearchParams();
    if (filters?.start_date) params.append("start_date", filters.start_date);
    if (filters?.end_date) params.append("end_date", filters.end_date);
    if (userId) params.append("user_id", userId);

    const queryString = params.toString() ? `?${params.toString()}` : "";
    const url = `${API_URL}/api/analytics/user-analytics/export/user-data${queryString}`;

    console.log(`Checking user export response: ${url}`);

    const response = await fetch(url);
    const contentType = response.headers.get("Content-Type") || "";

    if (contentType.includes("application/json")) {
      const errorData = await response.json();
      if (errorData.error === "date_range_required") {
        return {
          success: false,
          error: "date_range_required",
          message:
            errorData.message ??
            "Please select a date range to export user data.",
        };
      }
      return {
        success: false,
        message: errorData.message ?? "User export failed",
      };
    } else if (
      contentType.includes("spreadsheet") ??
      contentType.includes("excel")
    ) {
      console.log(
        `User analytics export successful${userId ? ` for user: ${userId}` : ""}`
      );
      window.open(url, "_blank");
      return { success: true };
    }
    return {
      success: false,
      message: "Unexpected response format from user export API",
    };
  } catch (error) {
    console.error(`User export failed:`, error);
    return {
      success: false,
      message: `User export failed: ${error instanceof Error ? error.message : "Unknown error"}`,
    };
  }
}

export async function testUserAnalyticsConnection(): Promise<{
  status: string;
  message: string;
  total_users?: number;
  total_queries?: number;
  total_sessions?: number;
}> {
  try {
    const url = `${API_URL}/api/analytics/user-analytics/test-connection`;
    console.log("🔍 Testing user analytics connection:", url);

    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(
        `Failed to test user analytics connection: ${response.status} ${response.statusText}`
      );
    }

    const data = await response.json();
    console.log(" User analytics connection test response:", data);

    return data;
  } catch (error) {
    console.error("Error testing user analytics connection:", error);
    return {
      status: "error",
      message:
        error instanceof Error ? error.message : "Connection test failed",
    };
  }
}

export async function exportQueryAnalyticsToExcelWithUser(
  exportType:
    | "all-queries"
    | "thumbs-up"
    | "thumbs-down"
    | "no-feedback"
    | "queries-with-fst-feedback",
  filters?: DateFilters,
  userId?: string
): Promise<{ success: boolean; message?: string; error?: string }> {
  try {
    console.log(
      `Starting export: ${exportType}${userId ? ` for user: ${userId}` : ""}`
    );

    const params = new URLSearchParams();
    if (filters?.start_date) params.append("start_date", filters.start_date);
    if (filters?.end_date) params.append("end_date", filters.end_date);
    if (userId) params.append("user_id", userId);

    const queryString = params.toString() ? `?${params.toString()}` : "";

    const endpointMap = {
      "all-queries": "/export/all-queries",
      "thumbs-up": "/export/thumbs-up",
      "thumbs-down": "/export/thumbs-down",
      "no-feedback": "/export/no-feedback",
      "queries-with-fst-feedback": "/export/queries-with-fst-feedback",
    };

    const endpoint = endpointMap[exportType];
    const url = `${API_URL}/api/analytics/query-analytics${endpoint}${queryString}`;

    console.log(`Checking export response: ${url}`);

    const response = await fetch(url);
    const contentType = response.headers.get("Content-Type") || "";

    if (contentType.includes("application/json")) {
      const errorData = await response.json();
      if (errorData.error === "date_range_required") {
        return {
          success: false,
          error: "date_range_required",
          message:
            errorData.message ?? "Please select a date range to export data.",
        };
      }
      return {
        success: false,
        message: errorData.message ?? "Export failed",
      };
    } else if (
      contentType.includes("spreadsheet") ??
      contentType.includes("excel")
    ) {
      console.log(
        `Real data export successful: ${exportType}${userId ? ` for user: ${userId}` : ""}`
      );
      return { success: true };
    }
    return {
      success: false,
      message: "Unexpected response format from export API",
    };
  } catch (error) {
    console.error(`Export failed:`, error);
    return {
      success: false,
      message: `Export failed: ${error instanceof Error ? error.message : "Unknown error"}`,
    };
  }
}

export async function fetchQueryAnalyticsMetricsWithUser(
  filters?: DateFilters,
  userId?: string
): Promise<{
  total_sessions: number;
  total_queries: number;
  total_unique_users: number;
  queries_per_session: number;
  repeat_queries_percentage: number;
  accuracy_percentage: number;
  voter_satisfaction_rate: number;
  engagement_rate: number;
  avg_response_time_seconds: number;
  avg_queries_per_day: number;
  avg_unique_users_per_day: number;
  thumbs_up_percentage: number;
  thumbs_down_percentage: number;
  no_vote_percentage: number;
  feedback_distribution: {
    type: string;
    count: number;
    percentage: number;
  }[];
  _source: string;
  _debug?: {
    total_voted: number;
    thumbs_up_count: number;
    thumbs_down_count: number;
    exact_repeats: number;
    sessions_with_repeats: number;
    total_analyzed: number;
    method1_percentages: string;
    method2_percentages: string;
    total_unique_users: number;
    avg_unique_users_per_day: number;
  };
}> {
  try {
    const params = new URLSearchParams();
    if (filters?.start_date) params.append("start_date", filters.start_date);
    if (filters?.end_date) params.append("end_date", filters.end_date);
    if (userId) params.append("user_id", userId);

    const queryString = params.toString() ? `?${params.toString()}` : "";
    const url = `${API_URL}/api/analytics/query-analytics/metrics${queryString}`;

    console.log(
      "Fetching query analytics metrics (with user filter) from:",
      url
    );

    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(
        `Failed to fetch query analytics metrics: ${response.status} ${response.statusText}`
      );
    }

    const data = await response.json();
    console.log("Query analytics metrics (with user filter) response:", data);

    return data;
  } catch (error) {
    console.error(
      "Error fetching query analytics metrics with user filter:",
      error
    );
    return {
      total_sessions: 0,
      total_queries: 0,
      total_unique_users: 0,
      queries_per_session: 0,
      repeat_queries_percentage: 0,
      accuracy_percentage: 0,
      voter_satisfaction_rate: 0,
      engagement_rate: 0,
      avg_response_time_seconds: 0,
      avg_queries_per_day: 0,
      avg_unique_users_per_day: 0,
      thumbs_up_percentage: 0,
      thumbs_down_percentage: 0,
      no_vote_percentage: 0,
      feedback_distribution: [],
      _source: "error_no_data",
    };
  }
}
export async function fetchQueryAnalyticsNoFeedbackQueries(
  filters?: DateFilters,
  limit = 50
): Promise<
  {
    query: string;
    response: string;
    timestamp: string;
    user: string;
    feedback: string;
    session_id: string;
  }[]
> {
  try {
    const params = new URLSearchParams();
    if (filters?.start_date) params.append("start_date", filters.start_date);
    if (filters?.end_date) params.append("end_date", filters.end_date);
    params.append("feedback_type", "no_feedback");
    params.append("limit", limit.toString());

    const queryString = `?${params.toString()}`;
    const url = `${API_URL}/api/analytics/query-analytics/feedback-queries${queryString}`;

    console.log("Fetching no feedback queries from:", url);

    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(
        `Failed to fetch no feedback queries: ${response.status} ${response.statusText}`
      );
    }

    const data = await response.json();
    console.log("No feedback queries response:", data.length, "queries");

    return data;
  } catch (error) {
    console.error("Error fetching no feedback queries:", error);
    return [];
  }
}

function validateDateRange(
  startDate?: string,
  endDate?: string
): {
  isValid: boolean;
  error?: string;
  validatedStart?: string;
  validatedEnd?: string;
} {
  if (!startDate && !endDate) {
    return { isValid: true };
  }

  try {
    let startDateTime: Date | null = null;
    let endDateTime: Date | null = null;

    if (startDate) {
      if (!/^\d{4}-\d{2}-\d{2}$/.test(startDate)) {
        return {
          isValid: false,
          error: "Start date must be in YYYY-MM-DD format",
        };
      }
      startDateTime = new Date(startDate);
      if (isNaN(startDateTime.getTime())) {
        return { isValid: false, error: "Invalid start date" };
      }
    }

    if (endDate) {
      if (!/^\d{4}-\d{2}-\d{2}$/.test(endDate)) {
        return {
          isValid: false,
          error: "End date must be in YYYY-MM-DD format",
        };
      }
      endDateTime = new Date(endDate);
      if (isNaN(endDateTime.getTime())) {
        return { isValid: false, error: "Invalid end date" };
      }
    }

    if (startDateTime && endDateTime && startDateTime > endDateTime) {
      return {
        isValid: false,
        error: "Start date must be less than or equal to end date",
      };
    }

    return {
      isValid: true,
      validatedStart: startDate,
      validatedEnd: endDate,
    };
  } catch (error) {
    return { isValid: false, error: "Date validation error" };
  }
}

function buildQueryString(filters?: DateFilters): string {
  if (
    !filters ||
    (!filters.start_date &&
      !filters.end_date &&
      !filters.manager_id &&
      !filters.fst_id &&
      !filters.product_type)
  )
    return "";

  const params = new URLSearchParams();

  if (filters.start_date || filters.end_date) {
    const validation = validateDateRange(filters.start_date, filters.end_date);
    if (!validation.isValid) {
      console.warn(`Date validation failed: ${validation.error}`);
      if (filters.manager_id !== null && filters.manager_id !== undefined) {
        params.append("manager_id", filters.manager_id.toString());
      }
      if (filters.fst_id !== null && filters.fst_id !== undefined) {
        params.append("fst_id", filters.fst_id.toString());
      }
      if (filters.product_type) {
        params.append("product_type", filters.product_type);
      }
      return params.toString() ? `?${params.toString()}` : "";
    }

    if (validation.validatedStart)
      params.append("start_date", validation.validatedStart);
    if (validation.validatedEnd)
      params.append("end_date", validation.validatedEnd);
  }

  if (filters.manager_id !== null && filters.manager_id !== undefined) {
    params.append("manager_id", filters.manager_id.toString());
  }

  if (filters.fst_id !== null && filters.fst_id !== undefined) {
    params.append("fst_id", filters.fst_id.toString());
  }

  if (filters.product_type !== null && filters.product_type !== undefined) {
    params.append("product_type", filters.product_type);
  }

  return `?${params.toString()}`;
}
export async function fetchServiceRequestTrends(
  filters?: DateFilters
): Promise<TrendData[]> {
  try {
    const validation = validateDateRange(
      filters?.start_date,
      filters?.end_date
    );
    if (!validation.isValid) {
      console.error(`Date validation failed for trends: ${validation.error}`);
      throw new Error(`Invalid date range: ${validation.error}`);
    }

    const queryString = buildQueryString(filters);
    const url = `${API_URL}/api/analytics/summary/trends${queryString}`;

    console.log(`Fetching SR trends from: ${url}`);

    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(
        `Failed to fetch trends: ${response.status} ${response.statusText}`
      );
    }

    const data = (await response.json()) as TrendData[];
    console.log(`Received ${data.length} trend data points`);

    return data;
  } catch (error) {
    console.error("Error fetching service request trends:", error);
    throw error;
  }
}

export async function fetchMachineDistribution(
  filters?: DateFilters
): Promise<DistributionData[]> {
  try {
    const validation = validateDateRange(
      filters?.start_date,
      filters?.end_date
    );
    if (!validation.isValid) {
      console.error(
        `Date validation failed for machine distribution: ${validation.error}`
      );
      throw new Error(`Invalid date range: ${validation.error}`);
    }

    const queryString = buildQueryString(filters);
    const url = `${API_URL}/api/analytics/summary/machine-distribution${queryString}`;

    console.log(`Fetching machine distribution from: ${url}`);

    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(
        `Failed to fetch machine distribution: ${response.status} ${response.statusText}`
      );
    }

    const data = (await response.json()) as DistributionData[];
    console.log(`Received ${data.length} machine types`);

    return data;
  } catch (error) {
    console.error("Error fetching machine distribution:", error);
    throw error;
  }
}

export async function fetchSeverityDistribution(
  filters?: DateFilters
): Promise<SeverityData[]> {
  try {
    const validation = validateDateRange(
      filters?.start_date,
      filters?.end_date
    );
    if (!validation.isValid) {
      console.error(
        `Date validation failed for severity distribution: ${validation.error}`
      );
      throw new Error(`Invalid date range: ${validation.error}`);
    }

    const queryString = buildQueryString(filters);
    const url = `${API_URL}/api/analytics/summary/severity-distribution${queryString}`;

    console.log(`Fetching severity distribution from: ${url}`);

    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(
        `Failed to fetch severity distribution: ${response.status} ${response.statusText}`
      );
    }

    const data = (await response.json()) as SeverityData[];
    console.log(`Received ${data.length} severity levels`);

    return data;
  } catch (error) {
    console.error("Error fetching severity distribution:", error);
    throw error;
  }
}

export async function fetchReplacedPartsOverview(
  filters?: DateFilters
): Promise<ReplacedPartsOverview> {
  try {
    const validation = validateDateRange(
      filters?.start_date,
      filters?.end_date
    );
    if (!validation.isValid) {
      console.warn(
        `Date validation failed for replaced parts: ${validation.error}`
      );
      filters = undefined;
    }

    const queryString = buildQueryString(filters);
    const response = await fetch(
      `${API_URL}/api/analytics/issues/replaced-parts-overview${queryString}`
    );

    if (!response.ok) {
      console.error(
        `Failed to fetch replaced parts overview: ${response.status} ${response.statusText}`
      );
      throw new Error("Failed to fetch replaced parts overview");
    }

    const data = await response.json();
    return data as ReplacedPartsOverview;
  } catch (error) {
    console.error("Error fetching replaced parts overview:", error);
    throw error;
  }
}

export async function fetchPartsToIssuesCorrelation(
  filters?: DateFilters
): Promise<PartsIssueCorrelation[]> {
  try {
    const validation = validateDateRange(
      filters?.start_date,
      filters?.end_date
    );
    if (!validation.isValid) {
      console.warn(
        `Date validation failed for parts-issues correlation: ${validation.error}`
      );
      filters = undefined;
    }

    const queryString = buildQueryString(filters);
    const response = await fetch(
      `${API_URL}/api/analytics/issues/parts-to-issues-correlation${queryString}`
    );

    if (!response.ok) {
      console.error(
        `Failed to fetch parts-issues correlation: ${response.status} ${response.statusText}`
      );
      throw new Error("Failed to fetch parts-issues correlation");
    }

    const data = await response.json();
    return data as PartsIssueCorrelation[];
  } catch (error) {
    console.error("Error fetching parts-issues correlation:", error);
    throw error;
  }
}

export async function fetchTopCustomers(
  filters?: DateFilters,
  limit?: number
): Promise<CustomerData[]> {
  try {
    let queryString = buildQueryString(filters);

    if (limit !== undefined && limit > 0) {
      if (queryString) {
        queryString += `&limit=${limit}`;
      } else {
        queryString = `?limit=${limit}`;
      }
    }

    const url = `${API_URL}/api/analytics/customer/top-customers${queryString}`;
    console.log("Fetching customers from:", url);

    const response = await fetch(url);
    if (!response.ok) throw new Error("Failed to fetch customers");
    return (await response.json()) as CustomerData[];
  } catch (error) {
    console.error("Error fetching top customers:", error);
    throw error;
  }
}

export async function fetchCustomerTopTechnicians(
  filters?: DateFilters & { customer_account: string }
): Promise<{
  top_technicians: Array<{
    name: string;
    count: number;
    avg_resolution_days: number;
  }>;
  customer_account: string;
}> {
  try {
    if (!filters?.customer_account) {
      throw new Error("customer_account is required");
    }

    let queryString = buildQueryString(filters);

    if (queryString) {
      queryString += `&customer_account=${filters.customer_account}`;
    } else {
      queryString = `?customer_account=${filters.customer_account}`;
    }

    const url = `${API_URL}/api/analytics/customer/customer-top-technicians${queryString}`;
    console.log("Fetching top technicians from:", url);

    const response = await fetch(url);

    if (!response.ok) {
      console.error(`Top technicians API failed: ${response.status} ${response.statusText}`);
      throw new Error(`Failed to fetch top technicians: ${response.status} ${response.statusText}`);
    }

    const data = await response.json();
    console.log("Top technicians response:", data);

    return data;
  } catch (error) {
    console.error("Error fetching top technicians:", error);
    return {
      top_technicians: [],
      customer_account: filters?.customer_account || ""
    };
  }
}


export async function fetchCustomerCount(filters?: DateFilters): Promise<{
  totalCustomers: number;
  totalServiceRequests: number;
}> {
  try {
    const validation = validateDateRange(
      filters?.start_date,
      filters?.end_date
    );
    if (!validation.isValid) {
      console.warn(
        `Date validation failed for customer count: ${validation.error}`
      );
      filters = undefined;
    }

    const params = new URLSearchParams();
    if (validation.isValid && filters?.start_date)
      params.append("start_date", filters.start_date);
    if (validation.isValid && filters?.end_date)
      params.append("end_date", filters.end_date);

    const queryString = params.toString() ? `?${params.toString()}` : "";
    const response = await fetch(
      `${API_URL}/api/analytics/customer/customer-count${queryString}`
    );

    if (!response.ok) throw new Error("Failed to fetch customer count");
    return await response.json();
  } catch (error) {
    console.error("Error fetching customer count:", error);
    throw error;
  }
}

export async function fetchCustomersPaginated(
  filters?: DateFilters,
  page: number = 1,
  pageSize: number = 50
): Promise<{
  customers: CustomerData[];
  pagination: {
    page: number;
    pageSize: number;
    totalCustomers: number;
    totalPages: number;
    hasNext: boolean;
    hasPrev: boolean;
  };
}> {
  try {
    const validation = validateDateRange(
      filters?.start_date,
      filters?.end_date
    );
    if (!validation.isValid) {
      console.warn(
        `Date validation failed for paginated customers: ${validation.error}`
      );
      filters = undefined;
    }

    const params = new URLSearchParams();
    if (validation.isValid && filters?.start_date)
      params.append("start_date", filters.start_date);
    if (validation.isValid && filters?.end_date)
      params.append("end_date", filters.end_date);
    params.append("page", page.toString());
    params.append("page_size", pageSize.toString());

    const queryString = `?${params.toString()}`;
    const response = await fetch(
      `${API_URL}/api/analytics/customer/customers-paginated${queryString}`
    );

    if (!response.ok) throw new Error("Failed to fetch paginated customers");
    return await response.json();
  } catch (error) {
    console.error("Error fetching paginated customers:", error);
    throw error;
  }
}

export async function fetchCustomerDistribution(
  filters?: DateFilters
): Promise<CustomerProportion[]> {
  try {
    const queryString = buildQueryString(filters);
    const response = await fetch(
      `${API_URL}/api/analytics/customer/customer-distribution${queryString}`
    );
    if (!response.ok) throw new Error("Failed to fetch customer distribution");
    return (await response.json()) as CustomerProportion[];
  } catch (error) {
    console.error("Error fetching customer distribution:", error);
    throw error;
  }
}

export async function fetchCustomerServiceRequests(
  filters?: DateFilters
): Promise<CustomerRequestData[]> {
  try {
    const validation = validateDateRange(
      filters?.start_date,
      filters?.end_date
    );
    if (!validation.isValid) {
      console.warn(
        `Date validation failed for customer service requests: ${validation.error}`
      );
      filters = undefined;
    }

    const queryString = buildQueryString(filters);
    const response = await fetch(
      `${API_URL}/api/analytics/customer/service-requests${queryString}`
    );
    if (!response.ok) throw new Error("Failed to fetch customer requests");
    return (await response.json()) as CustomerRequestData[];
  } catch (error) {
    console.error("Error fetching customer service requests:", error);
    throw error;
  }
}

export async function fetchCustomerHeatmap(
  filters?: DateFilters
): Promise<CustomerHeatmapData> {
  try {
    const validation = validateDateRange(
      filters?.start_date,
      filters?.end_date
    );
    if (!validation.isValid) {
      console.warn(
        `Date validation failed for customer heatmap: ${validation.error}`
      );
      filters = undefined;
    }

    const queryString = buildQueryString(filters);
    const response = await fetch(
      `${API_URL}/api/analytics/customer/customer-heatmap${queryString}`
    );
    if (!response.ok) throw new Error("Failed to fetch heatmap data");
    return (await response.json()) as CustomerHeatmapData;
  } catch (error) {
    console.error("Error fetching customer heatmap:", error);
    throw error;
  }
}

export async function fetchIssueConcentrations(
  filters?: DateFilters
): Promise<IssueConcentration> {
  try {
    const validation = validateDateRange(
      filters?.start_date,
      filters?.end_date
    );
    if (!validation.isValid) {
      console.warn(
        `Date validation failed for issue concentrations: ${validation.error}`
      );
      filters = undefined;
    }

    const queryString = buildQueryString(filters);
    const response = await fetch(
      `${API_URL}/api/analytics/customer/issue-concentrations${queryString}`
    );
    if (!response.ok) throw new Error("Failed to fetch issue concentrations");
    return (await response.json()) as IssueConcentration;
  } catch (error) {
    console.error("Error fetching issue concentrations:", error);
    throw error;
  }
}

export async function fetchMachineOverview(
  filters?: DateFilters
): Promise<MachineOverviewData> {
  try {
    console.log("🔍 fetchMachineOverview called with filters:", filters);

    const validation = validateDateRange(
      filters?.start_date,
      filters?.end_date
    );
    if (!validation.isValid) {
      console.warn(
        `Date validation failed for machine overview: ${validation.error}`
      );
      filters = undefined;
    }

    const queryString = buildQueryString(filters);
    const url = `${API_URL}/api/analytics/product/machine-overview${queryString}`;

    console.log("🌐 Fetching from URL:", url);

    const response = await fetch(url);

    console.log("📡 Response status:", response.status);
    console.log("📡 Response ok:", response.ok);

    if (!response.ok) {
      console.error(" Response not ok:", response.status, response.statusText);
      throw new Error("Failed to fetch machine overview");
    }

    const data = (await response.json()) as MachineOverviewData;

    console.log(" Raw backend response:", data);
    console.log("topModelsByType from backend:", data.topModelsByType);
    console.log("typeof topModelsByType:", typeof data.topModelsByType);
    console.log(
      " Array.isArray(topModelsByType):",
      Array.isArray(data.topModelsByType)
    );

    if (data.topModelsByType) {
      console.log(" topModelsByType length:", data.topModelsByType.length);
      console.log(" First item:", data.topModelsByType[0]);
    }

    return data;
  } catch (error) {
    console.error(" Error fetching machine overview:", error);
    throw error;
  }
}

export async function fetchMachineDetails(
  filters?: DateFilters
): Promise<MachineDetail[]> {
  try {
    const validation = validateDateRange(
      filters?.start_date,
      filters?.end_date
    );
    if (!validation.isValid) {
      console.warn(
        `Date validation failed for machine details: ${validation.error}`
      );
      filters = undefined;
    }

    const queryString = buildQueryString(filters);
    const response = await fetch(
      `${API_URL}/api/analytics/product/machine-details${queryString}`
    );
    if (!response.ok) throw new Error("Failed to fetch machine details");
    return (await response.json()) as MachineDetail[];
  } catch (error) {
    console.error("Error fetching machine details:", error);
    throw error;
  }
}

export async function fetchPartsAnalysis(
  filters?: DateFilters,
  limit = 50
): Promise<PartsData[]> {
  try {
    const validation = validateDateRange(
      filters?.start_date,
      filters?.end_date
    );
    if (!validation.isValid) {
      console.warn(
        `Date validation failed for parts analysis: ${validation.error}`
      );
      filters = undefined;
    }

    let queryString = buildQueryString(filters);
    if (queryString) {
      queryString += `&limit=${limit}`;
    } else {
      queryString = `?limit=${limit}`;
    }

    const response = await fetch(`${API_URL}/api/analytics/product/parts${queryString}`);

    if (!response.ok) {
      console.error(
        `Failed to fetch parts: ${response.status} ${response.statusText}`
      );
      throw new Error("Failed to fetch parts");
    }

    const data = await response.json();
    return data as PartsData[];
  } catch (error) {
    console.error("Error fetching parts analysis:", error);
    throw error;
  }
}

export async function fetchPartsByMachineType(
  filters?: DateFilters
): Promise<MachinePartsBreakdown[]> {
  try {
    const queryString = buildQueryString(filters);
    const url = `${API_URL}/api/analytics/product/parts-by-machine-type${queryString}`;

    console.log("Fetching parts by machine type from:", url);

    const response = await fetch(url);

    if (!response.ok) {
      console.error(
        `Parts by machine type API failed: ${response.status} ${response.statusText}`
      );
      throw new Error(
        `Failed to fetch parts by machine type: ${response.status} ${response.statusText}`
      );
    }

    const data = await response.json();
    console.log("Parts by machine type response:", data);

    return data as MachinePartsBreakdown[];
  } catch (error) {
    console.error("Error fetching parts by machine type:", error);
    throw error;
  }
}

export async function fetchPartsByMachineFiltered(
  filters?: DateFilters & { machine_type?: string }
): Promise<PartsData[]> {
  try {
    let queryString = buildQueryString(filters);

    // Then add machine_type if specified
    if (filters?.machine_type && filters.machine_type !== "all") {
      if (queryString) {
        queryString += `&machine_type=${filters.machine_type}`;
      } else {
        queryString = `?machine_type=${filters.machine_type}`;
      }
    }

    const url = `${API_URL}/api/analytics/product/parts-by-machine-filtered${queryString}`;

    console.log("Fetching parts by machine filtered from:", url);
    console.log("With filters:", filters);

    const response = await fetch(url);

    if (!response.ok) {
      console.error(
        `Parts by machine filtered API failed: ${response.status} ${response.statusText}`
      );
      throw new Error(
        `Failed to fetch parts by machine filtered: ${response.status} ${response.statusText}`
      );
    }

    const data = await response.json();
    console.log("Parts by machine filtered response:", data);
    console.log("Number of filtered parts:", data.length);

    return data as PartsData[];
  } catch (error) {
    console.error("Error fetching parts by machine filtered:", error);
    throw error;
  }
}

export async function fetchIssueStatistics(
  filters?: DateFilters
): Promise<IssueStatistics> {
  try {
    const validation = validateDateRange(
      filters?.start_date,
      filters?.end_date
    );
    if (!validation.isValid) {
      console.warn(
        `Date validation failed for issue statistics: ${validation.error}`
      );
      filters = undefined;
    }

    const queryString = buildQueryString(filters);
    const response = await fetch(
      `${API_URL}/api/analytics/issues/statistics${queryString}`
    );
    if (!response.ok) throw new Error("Failed to fetch issue statistics");
    return (await response.json()) as IssueStatistics;
  } catch (error) {
    console.error("Error fetching issue statistics:", error);
    throw error;
  }
}

export async function fetchIssueDistribution(
  filters?: DateFilters
): Promise<IssueCategoryData[]> {
  try {
    const validation = validateDateRange(
      filters?.start_date,
      filters?.end_date
    );
    if (!validation.isValid) {
      console.warn(
        `Date validation failed for issue distribution: ${validation.error}`
      );
      filters = undefined;
    }

    const queryString = buildQueryString(filters);
    const response = await fetch(
      `${API_URL}/api/analytics/issues/distribution${queryString}`
    );
    if (!response.ok) throw new Error("Failed to fetch issue distribution");
    return (await response.json()) as IssueCategoryData[];
  } catch (error) {
    console.error("Error fetching issue distribution:", error);
    throw error;
  }
}

export async function fetchIssueCategories(
  filters?: DateFilters
): Promise<CategoryBarData[]> {
  try {
    const validation = validateDateRange(
      filters?.start_date,
      filters?.end_date
    );
    if (!validation.isValid) {
      console.warn(
        `Date validation failed for issue categories: ${validation.error}`
      );
      filters = undefined;
    }

    const queryString = buildQueryString(filters);
    const response = await fetch(
      `${API_URL}/api/analytics/issues/categories${queryString}`
    );
    if (!response.ok) throw new Error("Failed to fetch issue categories");
    return (await response.json()) as CategoryBarData[];
  } catch (error) {
    console.error("Error fetching issue categories:", error);
    throw error;
  }
}

export async function fetchIssuesByMachineType(
  filters?: DateFilters
): Promise<MachineTypeIssue[]> {
  try {
    const validation = validateDateRange(
      filters?.start_date,
      filters?.end_date
    );
    if (!validation.isValid) {
      console.warn(
        `Date validation failed for issues by machine type: ${validation.error}`
      );
      filters = undefined;
    }

    const queryString = buildQueryString(filters);
    const response = await fetch(
      `${API_URL}/api/analytics/issues/by-machine-type${queryString}`
    );
    if (!response.ok) throw new Error("Failed to fetch issues by machine type");
    return (await response.json()) as MachineTypeIssue[];
  } catch (error) {
    console.error("Error fetching issues by machine type:", error);
    throw error;
  }
}

export async function fetchIssuesByCustomer(
  filters?: DateFilters
): Promise<CustomerTypeIssue[]> {
  try {
    const validation = validateDateRange(
      filters?.start_date,
      filters?.end_date
    );
    if (!validation.isValid) {
      console.warn(
        `Date validation failed for issues by customer: ${validation.error}`
      );
      filters = undefined;
    }

    const queryString = buildQueryString(filters);
    const response = await fetch(
      `${API_URL}/api/analytics/issues/by-customer${queryString}`
    );
    if (!response.ok) throw new Error("Failed to fetch issues by customer");
    return (await response.json()) as CustomerTypeIssue[];
  } catch (error) {
    console.error("Error fetching issues by customer:", error);
    throw error;
  }
}

export async function fetchServiceMetrics(
  filters?: DateFilters & { customer?: string }
): Promise<ServiceMetrics> {
  try {
    const validation = validateDateRange(
      filters?.start_date,
      filters?.end_date
    );
    if (!validation.isValid) {
      console.warn(
        `Date validation failed for service metrics: ${validation.error}`
      );
      filters = { customer: filters?.customer };
    }

    const params = new URLSearchParams();
    if (validation.isValid && filters?.start_date)
      params.append("start_date", filters.start_date);
    if (validation.isValid && filters?.end_date)
      params.append("end_date", filters.end_date);
    if (filters?.customer) params.append("customer", filters.customer);

    const queryString = params.toString() ? `?${params.toString()}` : "";
    const url = `${API_URL}/api/analytics/service/metrics${queryString}`;

    console.log("Fetching service metrics from:", url);
    console.log("With filters:", filters);

    const response = await fetch(url);

    if (!response.ok) {
      console.error(
        `Service metrics API failed: ${response.status} ${response.statusText}`
      );
      throw new Error(
        `Failed to fetch service metrics: ${response.status} ${response.statusText}`
      );
    }

    const data = (await response.json()) as ServiceMetrics;
    console.log("Service metrics response:", data);

    return data;
  } catch (error) {
    console.error("Error fetching service metrics:", error);
    throw error;
  }
}

export async function fetchTravelByRegion(
  filters?: DateFilters
): Promise<RegionTravelTime[]> {
  try {
    const validation = validateDateRange(
      filters?.start_date,
      filters?.end_date
    );
    if (!validation.isValid) {
      console.warn(
        `Date validation failed for travel by region: ${validation.error}`
      );
      filters = undefined;
    }

    const queryString = buildQueryString(filters);
    const response = await fetch(
      `${API_URL}/api/analytics/service/travel-by-region${queryString}`
    );
    if (!response.ok) throw new Error("Failed to fetch travel by region");
    return (await response.json()) as RegionTravelTime[];
  } catch (error) {
    console.error("Error fetching travel by region:", error);
    throw error;
  }
}

export async function fetchTechnicianPerformance(
  filters?: DateFilters
): Promise<TechnicianPerformance[]> {
  try {
    const validation = validateDateRange(
      filters?.start_date,
      filters?.end_date
    );
    if (!validation.isValid) {
      console.warn(
        `Date validation failed for technician performance: ${validation.error}`
      );
      filters = undefined;
    }

    const queryString = buildQueryString(filters);
    const response = await fetch(
      `${API_URL}/api/analytics/service/technician-performance${queryString}`
    );
    if (!response.ok) throw new Error("Failed to fetch technician performance");
    return (await response.json()) as TechnicianPerformance[];
  } catch (error) {
    console.error("Error fetching technician performance:", error);
    throw error;
  }
}

export async function fetchTimeAnalysis(
  filters?: DateFilters & { customer?: string }
): Promise<TimeAnalysis> {
  try {
    const validation = validateDateRange(
      filters?.start_date,
      filters?.end_date
    );
    if (!validation.isValid) {
      console.warn(
        `Date validation failed for time analysis: ${validation.error}`
      );
      filters = { customer: filters?.customer };
    }

    const params = new URLSearchParams();
    if (validation.isValid && filters?.start_date)
      params.append("start_date", filters.start_date);
    if (validation.isValid && filters?.end_date)
      params.append("end_date", filters.end_date);
    if (filters?.customer) params.append("customer", filters.customer);

    const queryString = params.toString() ? `?${params.toString()}` : "";
    const response = await fetch(
      `${API_URL}/api/analytics/service/time-analysis${queryString}`
    );
    if (!response.ok) throw new Error("Failed to fetch time analysis");
    return (await response.json()) as TimeAnalysis;
  } catch (error) {
    console.error("Error fetching time analysis:", error);
    throw error;
  }
}

export async function fetchCustomerParts(
  filters?: DateFilters & { customer_account?: string }
): Promise<unknown> {
  try {
    let queryString = buildQueryString(filters);

    if (filters?.customer_account) {
      if (queryString) {
        queryString += `&customer_account=${filters.customer_account}`;
      } else {
        queryString = `?customer_account=${filters.customer_account}`;
      }
    }

    const url = `${API_URL}/api/analytics/customer/customer-parts${queryString}`;
    console.log("Fetching customer parts from:", url);

    const response = await fetch(url);
    if (!response.ok) throw new Error("Failed to fetch customer parts data");
    return await response.json();
  } catch (error) {
    console.error("Error fetching customer parts data:", error);
    throw error;
  }
}

export async function fetchServiceValidationData(
  filters?: DateFilters & { customer?: string }
): Promise<unknown> {
  try {
    const validation = validateDateRange(
      filters?.start_date,
      filters?.end_date
    );
    if (!validation.isValid) {
      console.warn(
        `Date validation failed for service validation: ${validation.error}`
      );
      filters = { customer: filters?.customer };
    }

    const params = new URLSearchParams();
    if (validation.isValid && filters?.start_date)
      params.append("start_date", filters.start_date);
    if (validation.isValid && filters?.end_date)
      params.append("end_date", filters.end_date);
    if (filters?.customer) params.append("customer", filters.customer);

    const queryString = params.toString() ? `?${params.toString()}` : "";

    const response = await fetch(
      `${API_URL}/api/analytics/service/validate-data${queryString}`
    );
    if (!response.ok)
      throw new Error("Failed to fetch service validation data");
    return await response.json();
  } catch (error) {
    console.error("Error fetching service validation data:", error);
    throw error;
  }
}

export async function fetchCustomerResolutionTime(
  filters?: DateFilters & { customer_account?: string }
): Promise<unknown[]> {
  try {
    const validation = validateDateRange(
      filters?.start_date,
      filters?.end_date
    );
    if (!validation.isValid) {
      console.warn(
        `Date validation failed for customer resolution time: ${validation.error}`
      );
      filters = { customer_account: filters?.customer_account };
    }

    const params = new URLSearchParams();
    if (validation.isValid && filters?.start_date)
      params.append("start_date", filters.start_date);
    if (validation.isValid && filters?.end_date)
      params.append("end_date", filters.end_date);
    if (filters?.customer_account)
      params.append("customer_account", filters.customer_account);

    const queryString = params.toString() ? `?${params.toString()}` : "";
    const url = `${API_URL}/api/analytics/customer/customer-resolution-time${queryString}`;

    console.log("Fetching customer resolution time from:", url);

    const response = await fetch(url);

    if (!response.ok) {
      console.error(
        `Customer resolution time API failed: ${response.status} ${response.statusText}`
      );
      throw new Error(
        `Failed to fetch customer resolution time: ${response.status} ${response.statusText}`
      );
    }

    const data = await response.json();
    console.log("Customer resolution time response:", data);

    return data;
  } catch (error) {
    console.error("Error fetching customer resolution time:", error);
    return [];
  }
}

export async function fetchCustomerSeverityBreakdown(
  filters?: DateFilters & { customer_account?: string }
): Promise<any[]> {
  try {
    const validation = validateDateRange(
      filters?.start_date,
      filters?.end_date
    );
    if (!validation.isValid) {
      console.warn(
        `Date validation failed for customer severity breakdown: ${validation.error}`
      );
      filters = { customer_account: filters?.customer_account };
    }

    const params = new URLSearchParams();
    if (validation.isValid && filters?.start_date)
      params.append("start_date", filters.start_date);
    if (validation.isValid && filters?.end_date)
      params.append("end_date", filters.end_date);
    if (filters?.customer_account)
      params.append("customer_account", filters.customer_account);

    const queryString = params.toString() ? `?${params.toString()}` : "";
    const url = `${API_URL}/api/analytics/customer/customer-severity-breakdown${queryString}`;

    console.log("Fetching customer severity breakdown from:", url);

    const response = await fetch(url);
    if (!response.ok)
      throw new Error("Failed to fetch customer severity breakdown");

    const data = await response.json();
    console.log("Customer severity breakdown response:", data);
    return data;
  } catch (error) {
    console.error("Error fetching customer severity breakdown:", error);
    return [];
  }
}

export async function fetchCustomerDetailedMetrics(
  filters?: DateFilters & { customer_account: string }
): Promise<unknown> {
  try {
    if (!filters?.customer_account) {
      throw new Error("customer_account is required");
    }

    let queryString = buildQueryString(filters);

    if (queryString) {
      queryString += `&customer_account=${filters.customer_account}`;
    } else {
      queryString = `?customer_account=${filters.customer_account}`;
    }

    const url = `${API_URL}/api/analytics/customer/customer-detailed-metrics${queryString}`;
    console.log("Fetching customer detailed metrics from:", url);

    const response = await fetch(url);
    if (!response.ok)
      throw new Error("Failed to fetch customer detailed metrics");
    return await response.json();
  } catch (error) {
    console.error("Error fetching customer detailed metrics:", error);
    return null;
  }
}

export async function fetchServiceMachineDistribution(
  filters?: DateFilters & { customer?: string }
): Promise<any[]> {
  try {
    const validation = validateDateRange(
      filters?.start_date,
      filters?.end_date
    );
    if (!validation.isValid) {
      console.warn(
        `Date validation failed for service machine distribution: ${validation.error}`
      );
      filters = { customer: filters?.customer };
    }

    const params = new URLSearchParams();
    if (validation.isValid && filters?.start_date)
      params.append("start_date", filters.start_date);
    if (validation.isValid && filters?.end_date)
      params.append("end_date", filters.end_date);
    if (filters?.customer) params.append("customer", filters.customer);

    const queryString = params.toString() ? `?${params.toString()}` : "";
    const url = `${API_URL}/api/analytics/service/machine-distribution${queryString}`;

    console.log("Fetching service machine distribution from:", url);
    console.log("With filters:", filters);

    const response = await fetch(url);

    if (!response.ok) {
      console.error(
        `Service machine distribution API failed: ${response.status} ${response.statusText}`
      );
      throw new Error(
        `Failed to fetch service machine distribution: ${response.status} ${response.statusText}`
      );
    }

    const data = await response.json();
    console.log("Service machine distribution response:", data);

    return data;
  } catch (error) {
    console.error("Error fetching service machine distribution:", error);
    return [];
  }
}

export async function fetchChatbotResponse(
  userId: string,
  messageText: string,
  sessionId: string,
  chatbotV: ChatbotV,
  chatbotGenAi: ChatBotGenAI
): Promise<ChatMessageResponse> {
  const url = new URL(
    `${BACKEND_URL ?? ""}${chatbotV}?query=${messageText}&uid=${userId}&sid=${sessionId}&collection=${chatbotGenAi}`
  );
  const response = await fetch(url);
  if (!response.ok) throw new Error("Failed to fetch");
  const data: unknown = await response.json();
  if (isChatMessageResponse(data)) return data;
  throw new Error("Invalid data type");
}

export async function fetchSessionSummary(
  userId: string,
  sessionId: string
): Promise<SessionSummaryObject> {
  const url = new URL(
    `${BACKEND_URL ?? ""}summarization?uid=${userId}&sid=${sessionId}`
  );
  const response = await fetch(url);
  if (!response.ok) throw new Error("Failed to fetch");
  const data: unknown = await response.json();
  if (isSessionSummaryResponse(data)) return data;
  throw new Error("Invalid data type");
}

export async function debugDateFilters(filters?: DateFilters) {
  console.log("DEBUG: Date Filter Analysis");
  console.log("Raw filters:", filters);

  const validation = validateDateRange(filters?.start_date, filters?.end_date);
  console.log("Validation result:", validation);

  const queryString = buildQueryString(filters);
  console.log("Generated query string:", queryString);

  return {
    filters,
    validation,
    queryString,
    willShowAllTimeData: !queryString,
  };
}

export interface MachineFieldData {
  machineType: string;
  machineModel: string;
  totalSRs: number;
  machinesInField: number;
  srRate: number;
  uniqueMachinesWithSRs: number;
}

export interface MachineTypeSummary {
  machineType: string;
  totalMachinesInField: number;
  totalSRs: number;
  uniqueMachinesWithSRs: number;
  srRate: number;
}

export interface FieldDistributionResponse {
  fieldDistribution: MachineFieldData[];
  summary: {
    totalMachineTypesModels: number;
    avgSRRate: number;
    totalFieldPopulation: number;
    dateRange: {
      startDate: string | null;
      endDate: string | null;
    };
  };
}

const getApiUrl = () => {
  return process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
};

export const fetchMachineFieldDistribution = async (
  filters: DateFilters
): Promise<FieldDistributionResponse> => {
  try {
    const queryString = buildQueryString(filters);
    const url = `${API_URL}/api/analytics/product/machine-field-distribution${queryString}`;

    console.log("Fetching machine field distribution from:", url);

    const response = await fetch(url, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      throw new Error(
        `HTTP error! status: ${response.status} - ${response.statusText}`
      );
    }

    const data = await response.json();
    console.log("Field distribution response:", data);
    return data;
  } catch (error) {
    console.error("Error fetching machine field distribution:", error);
    throw error;
  }
};
export const fetchMachineTypeFieldSummary = async (
  filters: DateFilters
): Promise<MachineTypeSummary[]> => {
  try {
    const queryString = buildQueryString(filters);
    const url = `${API_URL}/api/analytics/product/machine-type-field-summary${queryString}`;

    console.log("Fetching machine type field summary from:", url);

    const response = await fetch(url, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      throw new Error(
        `HTTP error! status: ${response.status} - ${response.statusText}`
      );
    }

    const data = await response.json();
    console.log("Machine type field summary response:", data);
    return data;
  } catch (error) {
    console.error("Error fetching machine type field summary:", error);
    throw error;
  }
};
