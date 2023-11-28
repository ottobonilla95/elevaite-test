import { WorkbenchCard } from "@elevaite/ui";
import { ingestionMethods } from "../../dummydata";

export default function Page() {
  return (
    <div className="grid grid-cols-2 md:grid-cols-3 min-[1800px]:grid-cols-4 gap-4 p-8">
      {ingestionMethods.map((method) => (
        <WorkbenchCard
          key={method.iconAlt}
          description={method.description}
          icon={method.icon}
          iconAlt={method.iconAlt}
          subtitle={method.subtitle}
          title={method.title}
        />
      ))}
    </div>
  );
}
