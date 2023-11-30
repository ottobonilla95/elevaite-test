"use client";
import { WorkbenchCard } from "@elevaite/ui";
import { ingestionMethods } from "../../../dummydata";
import "./page.css";

export default function Page() {
  return (
    <div className="grid sm:max-lg:grid-cols-1 lg:max-2xl:grid-cols-2 2xl:grid-cols-3 3xl:grid-cols-4 gap-4 p-8 w-fit z-10">
      {ingestionMethods.map((method) => (
        <WorkbenchCard
          key={method.iconAlt}
          description={method.description}
          icon={method.icon}
          iconAlt={method.iconAlt}
          subtitle={method.subtitle}
          title={method.title}
          btnLabel="Description"
        />
      ))}
    </div>
  );
}
