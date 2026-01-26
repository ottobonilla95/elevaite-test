"use client";

import { useEffect, useState } from "react";
import type { JSX } from "react";

interface BackendEnvironmentInfo {
  environment: string;
  backend_url: string;
  service: string;
  worker_architecture: string;
  queue_system: string;
}

interface EnvironmentInfo {
  environment: string;
  backendUrl: string;
  frontendUrl: string;
  apiEnvironment?: string;
  service?: string;
  workerArchitecture?: string;
  queueSystem?: string;
}

export default function EnvironmentPage(): JSX.Element {
  const [envInfo, setEnvInfo] = useState<EnvironmentInfo>({
    environment: process.env.NODE_ENV ?? "unknown",
    backendUrl: process.env.NEXT_PUBLIC_BACKEND_URL ?? "unknown",
    frontendUrl:
      typeof window !== "undefined" ? window.location.origin : "unknown",
  });
  const [backendInfo, setBackendInfo] = useState<BackendEnvironmentInfo | null>(
    null,
  );
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchBackendEnvironment = async (): Promise<void> => {
      try {
        const backendUrl =
          process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8006";
        const response = await fetch(`${backendUrl}/environment`);

        if (!response.ok) {
          throw new Error(`HTTP ${response.status.toString()}`);
        }

        const data = (await response.json()) as BackendEnvironmentInfo;
        setBackendInfo(data);
        setEnvInfo((prev) => ({
          ...prev,
          apiEnvironment: data.environment,
          service: data.service,
          workerArchitecture: data.worker_architecture,
          queueSystem: data.queue_system,
        }));
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Failed to fetch backend info",
        );
      } finally {
        setLoading(false);
      }
    };

    void fetchBackendEnvironment();
  }, []);

  const getEnvironmentColor = (env: string): string => {
    switch (env.toLowerCase()) {
      case "production":
        return "bg-red-500";
      case "staging":
        return "bg-yellow-500";
      case "preview":
        return "bg-blue-500";
      case "development":
        return "bg-green-500";
      default:
        return "bg-gray-500";
    }
  };

  const currentEnv = backendInfo?.environment ?? envInfo.environment;

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-4xl mx-auto">
        {/* Header with Environment Badge */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            Environment Information
          </h1>
          <div
            className={`inline-flex items-center px-6 py-3 rounded-lg ${getEnvironmentColor(currentEnv)} text-white text-2xl font-bold uppercase`}
          >
            {currentEnv}
          </div>
        </div>

        {/* Frontend Info Card */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-2xl font-semibold text-gray-800 mb-4 flex items-center">
            <span className="mr-2">🌐</span> Frontend
          </h2>
          <div className="space-y-2">
            <InfoRow label="Environment" value={envInfo.environment} />
            <InfoRow label="Frontend URL" value={envInfo.frontendUrl} />
            <InfoRow label="Backend URL" value={envInfo.backendUrl} />
          </div>
        </div>

        {/* Backend Info Card */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-2xl font-semibold text-gray-800 mb-4 flex items-center">
            <span className="mr-2">⚙️</span> Backend
          </h2>
          {loading ? (
            <div className="text-gray-500">Loading backend info...</div>
          ) : error ? (
            <div className="text-red-500">Error: {error}</div>
          ) : backendInfo ? (
            <div className="space-y-2">
              <InfoRow label="Environment" value={backendInfo.environment} />
              <InfoRow label="Service" value={backendInfo.service} />
              <InfoRow
                label="Worker Architecture"
                value={backendInfo.worker_architecture}
              />
              <InfoRow label="Queue System" value={backendInfo.queue_system} />
            </div>
          ) : (
            <div className="text-gray-500">No backend info available</div>
          )}
        </div>

        {/* Architecture Info Card */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-2xl font-semibold text-gray-800 mb-4 flex items-center">
            <span className="mr-2">🏗️</span> Architecture
          </h2>
          <div className="space-y-3">
            <div className="flex items-center">
              <span className="font-medium text-gray-700 w-48">
                Worker Pattern:
              </span>
              <span className="text-green-600 font-semibold">
                ✓ Enabled (RabbitMQ Queue)
              </span>
            </div>
            <div className="flex items-center">
              <span className="font-medium text-gray-700 w-48">
                Deployment:
              </span>
              <span className="text-gray-900">
                {currentEnv === "development" ? "Local Docker" : "Kubernetes"}
              </span>
            </div>
            <div className="flex items-center">
              <span className="font-medium text-gray-700 w-48">
                Migration System:
              </span>
              <span className="text-green-600 font-semibold">
                ✓ Automated (Alembic)
              </span>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="mt-8 text-center text-gray-500 text-sm">
          <p>
            Access this page at:{" "}
            <code className="bg-gray-100 px-2 py-1 rounded">/environment</code>
          </p>
          <p className="mt-2">
            Backend endpoint:{" "}
            <code className="bg-gray-100 px-2 py-1 rounded">
              GET /environment
            </code>
          </p>
        </div>
      </div>
    </div>
  );
}

function InfoRow({
  label,
  value,
}: {
  label: string;
  value: string;
}): JSX.Element {
  return (
    <div className="flex items-center py-2 border-b border-gray-100 last:border-b-0">
      <span className="font-medium text-gray-700 w-48">{label}:</span>
      <span className="text-gray-900 font-mono text-sm">{value}</span>
    </div>
  );
}
