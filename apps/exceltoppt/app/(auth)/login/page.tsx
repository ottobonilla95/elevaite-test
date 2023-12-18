import { authenticate } from "@/app/lib/actions";
import { AuthFluff, LogInForm } from "@repo/ui/components";
import type { JSX } from "react";

function Login(): JSX.Element {
  return (
    <div className="ui-w-screen ui-h-screen">
      <div className="ui-flex ui-items-center ui-justify-center ui-bg-[#161616] ui-w-1/2 ui-h-full ui-float-left">
        <AuthFluff mode={1} />
      </div>
      <div className="ui-flex ui-items-center ui-justify-center ui-bg-[#282828] ui-h-full ui-w-1/2 ui-float-right">
        <LogInForm authenticate={authenticate} />
      </div>
    </div>
  );
}

export default Login;
