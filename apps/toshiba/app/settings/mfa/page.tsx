import { auth } from "../../../auth";
import { MFASettingsClient } from "./MFASettingsClient";

export default async function MFASettingsPage(): Promise<JSX.Element> {
  const session = await auth();

  return (
    <div className="ui-container ui-mx-auto ui-px-4 ui-py-8">
      <div className="ui-max-w-4xl ui-mx-auto">
        <div className="ui-mb-8">
          <h1 className="ui-text-3xl ui-font-bold ui-text-white ui-mb-2">
            Multi-Factor Authentication
          </h1>
          <p className="ui-text-gray-400">
            Secure your account with an additional layer of protection
          </p>
        </div>

        <MFASettingsClient
          user={session.user}
          accessToken={session.user.accessToken}
        />
      </div>
    </div>
  );
}
