"use client";
import { Card } from "@repo/ui/components";
import { Tab, Tabs, TabList, TabPanel } from "react-tabs";
import { ingestionMethods } from "../../../dummydata";
import "./page.scss";

export default function Page(): JSX.Element {
  return (
    <Tabs>
      <TabList>
        <Tab>INGEST</Tab>
        <Tab>TRAINING</Tab>
        <Tab>QA</Tab>
        <Tab>DEPLOY</Tab>
      </TabList>
      <TabPanel>
        <div className="tab-panel-contents ingest">
          {ingestionMethods.map((method) => (
            <Card
              btnLabel="Open"
              description={method.description}
              icon={method.icon}
              iconAlt={method.iconAlt}
              key={method.iconAlt}
              subtitle={method.subtitle}
              title={method.title}
            />
          ))}
        </div>
      </TabPanel>
      <TabPanel>
        <div className="grid sm:max-lg:grid-cols-1 lg:max-2xl:grid-cols-2 2xl:grid-cols-3 3xl:grid-cols-4 gap-4 p-8 w-fit">
          {ingestionMethods.map((method) => (
            <Card
              btnLabel="Open"
              description={method.description}
              icon={method.icon}
              iconAlt={method.iconAlt}
              key={method.iconAlt}
              subtitle={method.subtitle}
              title={method.title}
            />
          ))}
        </div>
      </TabPanel>
      <TabPanel>
        <div className="grid sm:max-lg:grid-cols-1 lg:max-2xl:grid-cols-2 2xl:grid-cols-3 3xl:grid-cols-4 gap-4 p-8 w-fit">
          {ingestionMethods.map((method) => (
            <Card
              btnLabel="Open"
              description={method.description}
              icon={method.icon}
              iconAlt={method.iconAlt}
              key={method.iconAlt}
              subtitle={method.subtitle}
              title={method.title}
            />
          ))}
        </div>
      </TabPanel>
      <TabPanel>
        <div className="grid sm:max-lg:grid-cols-1 lg:max-2xl:grid-cols-2 2xl:grid-cols-3 3xl:grid-cols-4 gap-4 p-8 w-fit">
          {ingestionMethods.map((method) => (
            <Card
              btnLabel="Open"
              description={method.description}
              icon={method.icon}
              iconAlt={method.iconAlt}
              key={method.iconAlt}
              subtitle={method.subtitle}
              title={method.title}
            />
          ))}
        </div>
      </TabPanel>
    </Tabs>
  );
}
