import type { SVGProps, JSX } from "react";

interface UploadHeaderProps {
  steps: { label: string; link: string; activated: boolean }[];
}

export function UploadHeader({ steps }: UploadHeaderProps): JSX.Element {
  // const pathname = usePathname();
  return (
    <div className="flex h-[80px] px-8 py-2.5 justify-between items-center flex-shrink-0 self-stretch border-b border-solid border-[#E5E5E5] bg-white">
      <div className="flex items-center gap-4">
        <ArrowLeft />
        <div className="flex flex-col items-start gap-1">
          {/* //TODO: Find out what these are */}
          <span className="heading text-[#171717] font-semibold">Page Title</span>
          <SubHeading parts={["Page Title 1", "Page Title 2", "Page Title 3"]} />
        </div>
      </div>
      <div className="flex items-start gap-16 relative">
        <line className="w-[614px] h-1 absolute right-[29.5px] top-1.5 -z-0 bg-[#ECEFF3]" />
        {steps.map((step) => (
          <div className="flex flex-col items-center gap-2" key={step.link}>
            {step.activated ? (
              <ActivatedFlow className="w-4 h-4 flex flex-1 items-center justify-center overflow-visible rounded-full z-10" />
            ) : (
              <InactiveFlow className="z-10" />
            )}
            <p className={`font-medium ${step.activated ? "text-black" : "text-[#A4ACB9]"} text-sm`}>{step.label}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

function ArrowLeft(props: SVGProps<SVGSVGElement>): JSX.Element {
  return (
    <svg fill="none" height={20} width={20} xmlns="http://www.w3.org/2000/svg" {...props}>
      <path
        d="M16.667 10H3.333m0 0 5 5m-5-5 5-5"
        stroke="#171717"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
      />
    </svg>
  );
}

function SubHeading({ parts }: { parts: string[] }): JSX.Element {
  return (
    <div className="flex items-start gap-2 text-xs font-semibold">
      {parts.map((part, index, array) => (
        <>
          <span>{part}</span> {index === array.length - 1 ? null : <span>/</span>}
        </>
      ))}
    </div>
  );
}

function ActivatedFlow(props: SVGProps<SVGSVGElement>): JSX.Element {
  return (
    <svg fill="none" height={16} width={16} xmlns="http://www.w3.org/2000/svg" {...props}>
      <g clipPath="url(#a)">
        <circle cx={8} cy={8} fill="#fff" r={7.5} stroke="#000" />
        <circle cx={8} cy={8} fill="#000" r={2} />
      </g>
      <defs>
        <clipPath id="a">
          <path d="M0 0h16v16H0z" fill="#fff" />
        </clipPath>
      </defs>
    </svg>
  );
}

function InactiveFlow(props: SVGProps<SVGSVGElement>): JSX.Element {
  return (
    <svg fill="none" height={16} width={16} xmlns="http://www.w3.org/2000/svg" {...props}>
      <g clipPath="url(#a)">
        <circle cx={8} cy={8} fill="#fff" r={7.5} stroke="#DFE1E7" />
        <circle cx={8} cy={8} fill="#DFE1E7" r={2} />
      </g>
      <defs>
        <clipPath id="a">
          <path d="M0 0h16v16H0z" fill="#fff" />
        </clipPath>
      </defs>
    </svg>
  );
}
