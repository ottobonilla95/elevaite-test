"use client";

import { logout } from "../lib/actions";

export function LogoutButton() {
  return (
    <button
      onClick={async () => {
        await logout();
      }}
      className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 transition-colors"
    >
      Sign Out
    </button>
  );
}
