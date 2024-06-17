"use client";
import { Card, ElevaiteIcons } from "@repo/ui/components";
import { useThemes } from "@repo/ui/contexts";
import { Tab, TabList, TabPanel, Tabs } from "react-tabs";
import { useWorkbench } from "../../lib/contexts/WorkbenchContext";
import "./page.scss";




export default function Page(): JSX.Element {
  const workbenchContext = useWorkbench();
  const themesContext = useThemes();


  return (
    <div className={["applications-page-container", themesContext.type].filter(Boolean).join(" ")}>
      <Tabs>
        <TabList>
          <Tab>INGEST</Tab>
          {/* <Tab>TRAINING</Tab>
          <Tab>QA</Tab>
          <Tab>DEPLOY</Tab> */}
        </TabList>
        <TabPanel>
          <div className="tab-panel-contents ingest">
            <Section separator>Data Retrieval Applications</Section>

            { workbenchContext.loading.applications === undefined ? null
            : workbenchContext.loading.applications ? 
              <Section><div className="loading-box"><ElevaiteIcons.SVGSpinner/><span>Loading Applications. Please wait...</span></div></Section>
            : workbenchContext.errors.applications ? 
              <Section><span>There has been an error loading the applications. Please try again later.</span></Section>
            :  workbenchContext.ingestList.length === 0 ?
              <Section>There are no data retrieval applications to display.</Section>
            : workbenchContext.ingestList.map((app) => (
                <Card
                  key={app.id}
                  id={app.id}
                  description={app.description}
                  icon={app.icon}
                  subtitle={`By ${app.creator}`}
                  title={app.title}
                  btnLabel="Open"
                  externalUrl={app.externalUrl}
                  openInNewTab={app.openInNewTab}
                  url={app.url ?? "/application"}
                />
              ))
            }

            <Section separator>Preprocess Applications</Section>

            { workbenchContext.loading.applications === undefined ? null
            : workbenchContext.loading.applications ? 
              <Section><div className="loading-box"><ElevaiteIcons.SVGSpinner/><span>Loading Applications. Please wait...</span></div></Section>
            : workbenchContext.errors.applications ? 
              <Section><span>There has been an error loading the applications. Please try again later.</span></Section>
            :  workbenchContext.preProcessingList.length === 0 ?
              <Section>There are no preprocessing applications to display.</Section>
            : workbenchContext.preProcessingList.map((app) => (
                <Card
                  key={app.id}
                  id={app.id}
                  description={app.description}
                  icon={app.icon}
                  subtitle={`By ${app.creator}`}
                  title={app.title}
                  btnLabel="Open"
                  externalUrl={app.externalUrl}
                  openInNewTab={app.openInNewTab}
                  url={app.url ?? "/application"}
                />
              ))
            }

          </div>
        </TabPanel>
        {/* <TabPanel>
          <div className="grid sm:max-lg:grid-cols-1 lg:max-2xl:grid-cols-2 2xl:grid-cols-3 3xl:grid-cols-4 gap-4 p-8 w-fit">
            {ingestionMethods.map((method) => (
              <Card
                key={method.id}
                id={method.id}
                btnLabel="Open"
                description={method.description}
                icon={method.icon}
                iconAlt={method.iconAlt}
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
                key={method.id}
                id={method.id}
                btnLabel="Open"
                description={method.description}
                icon={method.icon}
                iconAlt={method.iconAlt}
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
                key={method.id}
              id={method.id}
                btnLabel="Open"
                description={method.description}
                icon={method.icon}
                iconAlt={method.iconAlt}
                subtitle={method.subtitle}
                title={method.title}
              />
            ))}
          </div>
        </TabPanel> */}
      </Tabs>
    </div>
  );
}



function Section(props: { separator?: boolean, children?: React.ReactNode }): JSX.Element {
  return (
    <div className={["app-section", !props.separator ? "info" : undefined].filter(Boolean).join(" ")}>
      <span>{props.children}</span>
      {!props.separator ? null :
        <div className="separator"/>
      }
    </div>
  );
}
