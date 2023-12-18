import { AuthFluff, SignUpForm } from "@repo/ui/components";
import type { JSX } from "react";

function SignUp(): JSX.Element {
  return (
    <div className="ui-w-screen ui-h-screen">
      <div className="ui-flex ui-items-center ui-justify-center ui-bg-[#161616] ui-w-1/2 ui-h-full ui-float-left">
        <AuthFluff mode={1} />
      </div>
      <div className="ui-flex ui-items-center ui-justify-center ui-bg-[#282828] ui-h-full ui-w-1/2 ui-float-right">
        <SignUpForm />
      </div>
    </div>
  );
}

export default SignUp;
