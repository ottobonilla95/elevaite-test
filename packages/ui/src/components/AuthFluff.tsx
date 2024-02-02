import type { JSX, SVGProps } from "react";
import { Typewriter } from "./Typewriter";
import "./AuthFluff.scss";


interface AuthFluffProps {
  mode: 1 | 2;
}

export function AuthFluff({ mode }: AuthFluffProps): JSX.Element {
  return (
    <>
      {mode === 1 ? (
        <div className="auth-fluff-main-container">

          <div className="auth-fluff-box">
            <div className="auth-fluff-box-icon"><Inbox /></div>
            <div className="auth-fluff-box-text">
              <span>Reliable & Secure Enterprise</span>
              <Typewriter speed={250} stallCycles={4} texts={[" Gen"]} />
              <span> AI For the Future.</span>
            </div>
          </div>

          <div className="auth-fluff-box">
            <div className="auth-fluff-box-icon"><Trouble /></div>
            <div className="auth-fluff-box-text">
              <Typewriter
                  speed={50}
                  stallCycles={4}
                  texts={[
                    "Iterate, build and deploy your enterprise models faster...",
                    "Out of the box domain specific models and apps to build on...",
                    "Connect your models to your enterprise apps...",
                  ]}
                />
            </div>
          </div>

        </div>
      ) : (
        <div className="ui-flex ui-items-start ui-bg-[#161616] ui-w-1/2 ui-h-full ui-float-left">
          <div className="ui-p-10">
            <span className="ui-text-[#F7F7F7] ui-font-bold ui-font-source_sans ui-text-3xl">Sign in to ElevAIte</span>
            <div className="ui-flex ui-flex-row ui-items-center">
              <div className="ui-flex ui-items-center ui-justify-center ui-w-[60px] ui-h-[60px]  ui-flex-shrink-0">
                <Trouble />
              </div>
              <Typewriter
                className="ui-font-inter ui-line-clamp-2"
                speed={50}
                stallCycles={4}
                texts={[
                  "Iterate, build and deploy your enterprise models faster...",
                  "Out of the box domain specific models and apps to build on...",
                  "Connect your models to your enterprise apps...",
                ]}
              />
            </div>
          </div>
        </div>
      )}{" "}
    </>
  );
}

function Inbox(props: SVGProps<SVGSVGElement>): JSX.Element {
  return (
    <svg fill="none" height={20} width={20} xmlns="http://www.w3.org/2000/svg" {...props}>
      <path
        d="M19.963 9.448 17.94 3.952a.649.649 0 0 0-.615-.408l-4.631.004c.306.098.572.291.735.562.122.203.174.43.163.655l3.228-.004 1.838 4.965h-3.99c-.736 0-1.333.554-1.333 1.236v.619H6.667v-.618c0-.683-.597-1.237-1.333-1.237H1.342l1.762-4.947 3.57-.005a1.15 1.15 0 0 1 .16-.662c.16-.27.423-.46.726-.56l-4.888.004a.65.65 0 0 0-.615.408L.034 9.456A.566.566 0 0 0 0 9.649v8.115C0 18.446.597 19 1.333 19h17.334c.735 0 1.333-.554 1.333-1.236V9.649a.585.585 0 0 0-.037-.2Z"
        fill="#0ECC8D"
      />
      <path
        d="M7.418 4.41a.58.58 0 0 0 .017.628l2.13 3.161a.68.68 0 0 0 .566.29c.23 0 .444-.11.566-.29l2.13-3.162a.58.58 0 0 0 .018-.627.674.674 0 0 0-.583-.319h-.797V1.618c0-.342-.298-.618-.666-.618H9.465c-.368 0-.666.276-.666.618v2.473h-.797a.676.676 0 0 0-.584.32Z"
        fill="#0ECC8D"
      />
    </svg>
  );
}

function Trouble(props: SVGProps<SVGSVGElement>): JSX.Element {
  return (
    <svg fill="none" height={20} width={20} xmlns="http://www.w3.org/2000/svg" {...props}>
      <path
        d="M5.758 19.31c-.677.58-1.626-.016-1.382-.824l2.174-7.214c.035-.116-.006-.188-.124-.215l-2.34-.558c-.82-.195-1.01-1.23-.35-1.753L13.82.26c.677-.58 1.626.017 1.383.824L13.029 8.3c-.035.116.006.187.123.215l2.341.558c.82.195 1.01 1.23.35 1.753L5.758 19.31Z"
        fill="#EA942C"
      />
    </svg>
  );
}
