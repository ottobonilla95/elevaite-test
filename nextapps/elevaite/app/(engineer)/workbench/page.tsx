"use client";
import { Card } from "@elevaite/ui";
import { ingestionMethods } from "../../../dummydata";
import { Tab, Tabs, TabList, TabPanel } from "react-tabs";
import "./page.css";

export default function Page() {
  return (
    <Tabs>
      <TabList>
        <Tab>INGEST</Tab>
        <Tab>TRAINING</Tab>
        <Tab>QA</Tab>
        <Tab>DEPLOY</Tab>
      </TabList>
      <TabPanel>
        <div className="grid sm:max-lg:grid-cols-1 lg:max-2xl:grid-cols-2 2xl:grid-cols-3 3xl:grid-cols-4 gap-4 p-8 w-fit">
          {ingestionMethods.map((method) => (
            <Card
              key={method.iconAlt}
              description={method.description}
              icon={method.icon}
              iconAlt={method.iconAlt}
              subtitle={method.subtitle}
              title={method.title}
              btnLabel="Open"
              withHighlight
            />
          ))}
        </div>
      </TabPanel>
      <TabPanel>
        <div className="grid sm:max-lg:grid-cols-1 lg:max-2xl:grid-cols-2 2xl:grid-cols-3 3xl:grid-cols-4 gap-4 p-8 w-fit">
          {ingestionMethods.map((method) => (
            <Card
              key={method.iconAlt}
              description={method.description}
              icon={method.icon}
              iconAlt={method.iconAlt}
              subtitle={method.subtitle}
              title={method.title}
              btnLabel="Open"
              withHighlight
            />
          ))}
        </div>
      </TabPanel>
      <TabPanel>
        <div className="grid sm:max-lg:grid-cols-1 lg:max-2xl:grid-cols-2 2xl:grid-cols-3 3xl:grid-cols-4 gap-4 p-8 w-fit">
          {ingestionMethods.map((method) => (
            <Card
              key={method.iconAlt}
              description={method.description}
              icon={method.icon}
              iconAlt={method.iconAlt}
              subtitle={method.subtitle}
              title={method.title}
              btnLabel="Open"
              withHighlight
            />
          ))}
        </div>
      </TabPanel>
      <TabPanel>
        <div className="grid sm:max-lg:grid-cols-1 lg:max-2xl:grid-cols-2 2xl:grid-cols-3 3xl:grid-cols-4 gap-4 p-8 w-fit">
          {ingestionMethods.map((method) => (
            <Card
              key={method.iconAlt}
              description={method.description}
              icon={method.icon}
              iconAlt={method.iconAlt}
              subtitle={method.subtitle}
              title={method.title}
              btnLabel="Open"
              withHighlight
            />
          ))}
        </div>
      </TabPanel>
    </Tabs>
  );
}
