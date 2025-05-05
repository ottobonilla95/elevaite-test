import { ElevaiteIcons } from "@repo/ui/components";
import Link from "next/link";
import { auth } from "../../auth";
import { LogoutButton } from "../components/LogoutButton";

export default async function Home() {
  const session = await auth();

  return (
    <div className="flex flex-col items-center justify-center min-h-screen p-4">
      <div className="flex flex-col items-center justify-center space-y-4">
        <ElevaiteIcons.SVGNavbarLogo />
        <h1 className="text-3xl font-bold">Welcome to Toshiba Admin</h1>
        <p className="text-xl">This is the Toshiba Admin application</p>

        <div className="mt-4 flex flex-col gap-2">
          <Link
            href="/access"
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
          >
            Access Management
          </Link>
        </div>

        {session?.user && (
          <div className="mt-8 p-4 bg-gray-100 dark:bg-gray-800 rounded-lg">
            <h2 className="text-xl font-semibold mb-2">User Information</h2>
            <p>
              <strong>Name:</strong> {session.user.name}
            </p>
            <p>
              <strong>Email:</strong> {session.user.email}
            </p>
            <div className="mt-4">
              <LogoutButton />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
