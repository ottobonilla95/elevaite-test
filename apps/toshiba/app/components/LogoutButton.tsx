"use client";

import { clientLogout } from "../lib/clientLogout";

export function LogoutButton() {
  const handleLogout = async () => {
    await clientLogout();
  };

  return (
    <button
      onClick={handleLogout}
      className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 transition-colors"
    >
      Sign Out
    </button>
  );
}
