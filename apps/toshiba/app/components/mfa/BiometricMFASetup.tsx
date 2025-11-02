"use client";

import { useState, useEffect } from "react";
import { useSession } from "next-auth/react";

interface BiometricDevice {
    id: number;
    device_name: string;
    device_model?: string;
    is_active: boolean;
    last_used_at?: string;
    created_at: string;
}

interface BiometricMFASetupProps {
    enabled: boolean;
    onStatusChange?: (enabled: boolean) => void;
    onSuccess?: (message: string) => void;
    onError?: (message: string) => void;
}

export function BiometricMFASetup({
    enabled,
    onStatusChange,
    onSuccess,
    onError,
}: BiometricMFASetupProps): JSX.Element {
    const [devices, setDevices] = useState<BiometricDevice[]>([]);
    const [loading, setLoading] = useState(true);
    const [registering, setRegistering] = useState(false);
    const { data: session } = useSession();

    useEffect(() => {
        if (enabled) {
            loadDevices();
        } else {
            setLoading(false);
        }
    }, [enabled]);

    const loadDevices = async () => {
        if (!session?.authToken) return;

        try {
            const response = await fetch(
                `${process.env.NEXT_PUBLIC_AUTH_API_URL}/api/biometric/devices`,
                {
                    headers: {
                        Authorization: `Bearer ${session.authToken}`,
                        "X-Tenant-ID": process.env.NEXT_PUBLIC_AUTH_TENANT_ID || "default",
                    },
                }
            );

            if (response.ok) {
                const data = await response.json();
                setDevices(data);
            }
        } catch (error) {
            console.error("Failed to load devices:", error);
        } finally {
            setLoading(false);
        }
    };

    const registerDevice = async () => {
        if (!session?.authToken) return;

        setRegistering(true);
        try {
            // Check if WebAuthn is supported
            if (!window.PublicKeyCredential) {
                onError?.("Biometric authentication is not supported on this device");
                return;
            }

            // Generate a random challenge
            const challenge = new Uint8Array(32);
            window.crypto.getRandomValues(challenge);

            // Get device fingerprint
            const deviceFingerprint = `${navigator.userAgent}-${Date.now()}`;

            // Create credential options
            const publicKeyCredentialCreationOptions: PublicKeyCredentialCreationOptions =
            {
                challenge: challenge,
                rp: {
                    name: "Elevaite",
                    id: window.location.hostname,
                },
                user: {
                    id: new Uint8Array(16),
                    name: session.user?.email || "user@example.com",
                    displayName: session.user?.name || "User",
                },
                pubKeyCredParams: [{ alg: -7, type: "public-key" }],
                authenticatorSelection: {
                    authenticatorAttachment: "platform",
                    userVerification: "required",
                },
                timeout: 60000,
                attestation: "none",
            };

            // Create credential
            const credential = (await navigator.credentials.create({
                publicKey: publicKeyCredentialCreationOptions,
            })) as PublicKeyCredential;

            if (!credential) {
                throw new Error("Failed to create credential");
            }

            // Get public key
            const response =
                credential.response as AuthenticatorAttestationResponse;
            const publicKeyBuffer = response.getPublicKey();

            if (!publicKeyBuffer) {
                throw new Error("No public key returned");
            }

            const publicKey = btoa(
                String.fromCharCode(...new Uint8Array(publicKeyBuffer))
            );

            // Register device with backend
            const registerResponse = await fetch(
                `${process.env.NEXT_PUBLIC_AUTH_API_URL}/api/biometric/register`,
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        Authorization: `Bearer ${session.authToken}`,
                        "X-Tenant-ID": process.env.NEXT_PUBLIC_AUTH_TENANT_ID || "default",
                    },
                    body: JSON.stringify({
                        device_fingerprint: deviceFingerprint,
                        device_name: `${navigator.platform} Device`,
                        device_model:
                            navigator.userAgent.split("(")[1]?.split(")")[0] || "Unknown",
                        public_key: publicKey,
                    }),
                }
            );

            if (registerResponse.ok) {
                onSuccess?.("Biometric device registered successfully");
                loadDevices();
                onStatusChange?.(true);
            } else {
                const error = await registerResponse.json();
                onError?.(error.detail || "Failed to register device");
            }
        } catch (error) {
            console.error("Registration error:", error);
            onError?.(
                error instanceof Error
                    ? error.message
                    : "Failed to register biometric device"
            );
        } finally {
            setRegistering(false);
        }
    };

    const removeDevice = async (deviceId: number) => {
        if (!session?.authToken) return;

        try {
            const response = await fetch(
                `${process.env.NEXT_PUBLIC_AUTH_API_URL}/api/biometric/devices/${deviceId}`,
                {
                    method: "DELETE",
                    headers: {
                        Authorization: `Bearer ${session.authToken}`,
                        "X-Tenant-ID": process.env.NEXT_PUBLIC_AUTH_TENANT_ID || "default",
                    },
                }
            );

            if (response.ok) {
                onSuccess?.("Device removed successfully");
                const updatedDevices = devices.filter((d) => d.id !== deviceId);
                setDevices(updatedDevices);

                // If no devices left, notify parent that biometric is disabled
                if (updatedDevices.length === 0) {
                    onStatusChange?.(false);
                }
            } else {
                onError?.("Failed to remove device");
            }
        } catch (error) {
            console.error("Failed to remove device:", error);
            onError?.("Failed to remove device");
        }
    };

    if (!enabled) {
        return (
            <div className="ui-max-w-md ui-mx-auto ui-p-6 ui-bg-[#1a1a1a] ui-rounded-lg">
                <div className="ui-text-center ui-mb-6">
                    <h2 className="ui-text-2xl ui-font-bold ui-text-white ui-mb-2">
                        Biometric Authentication
                    </h2>
                    <p className="ui-text-gray-400">
                        Use fingerprint, face recognition, or other biometric methods to
                        sign in
                    </p>
                </div>

                <div className="ui-flex ui-justify-center">
                    <button
                        onClick={registerDevice}
                        disabled={registering}
                        className="ui-py-3 ui-px-4 ui-bg-[#E75F33] ui-text-white ui-rounded-lg ui-font-medium hover:ui-bg-[#d54d26] ui-transition-colors disabled:ui-opacity-50"
                    >
                        {registering ? "Setting up..." : "Enable Biometric Authentication"}
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="ui-max-w-md ui-mx-auto ui-p-6 ui-bg-[#1a1a1a] ui-rounded-lg">
            <div className="ui-text-center ui-mb-6">
                <h2 className="ui-text-2xl ui-font-bold ui-text-white ui-mb-2">
                    Biometric Authentication
                </h2>
                <p className="ui-text-gray-400">Manage your registered biometric devices</p>
            </div>

            {loading ? (
                <div className="ui-text-center ui-py-6">
                    <p className="ui-text-gray-400">Loading devices...</p>
                </div>
            ) : devices.length === 0 ? (
                <div className="ui-text-center ui-py-6">
                    <p className="ui-text-gray-400 ui-mb-4">No devices registered yet</p>
                    <button
                        onClick={registerDevice}
                        disabled={registering}
                        className="ui-py-3 ui-px-4 ui-bg-[#E75F33] ui-text-white ui-rounded-lg ui-font-medium hover:ui-bg-[#d54d26] ui-transition-colors disabled:ui-opacity-50"
                    >
                        {registering ? "Registering..." : "Register This Device"}
                    </button>
                </div>
            ) : (
                <div className="ui-space-y-4">
                    <div className="ui-space-y-3">
                        {devices.map((device) => (
                            <div
                                key={device.id}
                                className="ui-flex ui-items-center ui-justify-between ui-p-3 ui-border ui-border-gray-700 ui-rounded-lg"
                            >
                                <div className="ui-flex ui-items-center ui-gap-3">
                                    <svg
                                        className="ui-h-5 ui-w-5 ui-text-[#E75F33]"
                                        fill="none"
                                        stroke="currentColor"
                                        viewBox="0 0 24 24"
                                    >
                                        <path
                                            strokeLinecap="round"
                                            strokeLinejoin="round"
                                            strokeWidth={2}
                                            d="M12 11c0 3.517-1.009 6.799-2.753 9.571m-3.44-2.04l.054-.09A13.916 13.916 0 008 11a4 4 0 118 0c0 1.017-.07 2.019-.203 3m-2.118 6.844A21.88 21.88 0 0015.171 17m3.839 1.132c.645-2.266.99-4.659.99-7.132A8 8 0 008 4.07M3 15.364c.64-1.319 1-2.8 1-4.364 0-1.457.39-2.823 1.07-4"
                                        />
                                    </svg>
                                    <div>
                                        <p className="ui-font-medium ui-text-sm ui-text-white">
                                            {device.device_name}
                                        </p>
                                        {device.device_model && (
                                            <p className="ui-text-xs ui-text-gray-400">
                                                {device.device_model}
                                            </p>
                                        )}
                                        <p className="ui-text-xs ui-text-gray-400">
                                            Added{" "}
                                            {new Date(device.created_at).toLocaleDateString()}
                                        </p>
                                    </div>
                                </div>
                                <button
                                    onClick={() => removeDevice(device.id)}
                                    className="ui-p-2 ui-text-red-500 hover:ui-text-red-600 ui-transition-colors"
                                >
                                    <svg
                                        className="ui-h-5 ui-w-5"
                                        fill="none"
                                        stroke="currentColor"
                                        viewBox="0 0 24 24"
                                    >
                                        <path
                                            strokeLinecap="round"
                                            strokeLinejoin="round"
                                            strokeWidth={2}
                                            d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                                        />
                                    </svg>
                                </button>
                            </div>
                        ))}
                    </div>
                    <button
                        onClick={registerDevice}
                        disabled={registering}
                        className="ui-w-full ui-py-3 ui-px-4 ui-bg-[#E75F33] ui-text-white ui-rounded-lg ui-font-medium hover:ui-bg-[#d54d26] ui-transition-colors disabled:ui-opacity-50"
                    >
                        {registering ? "Registering..." : "Register Another Device"}
                    </button>
                </div>
            )}
        </div>
    );
}