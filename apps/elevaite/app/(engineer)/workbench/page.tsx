"use client";
import { Card, ElevaiteIcons } from "@repo/ui/components";
import { useEffect, useState } from "react";
import { Tab, TabList, TabPanel, Tabs } from "react-tabs";
import { ingestionMethods } from "../../../dummydata";
import { getApplicationList } from "../../lib/actions";
import type { ApplicationObject } from "../../lib/interfaces";
import { ApplicationType } from "../../lib/interfaces";
import "./page.scss";




export default function Page(): JSX.Element {
  const [applicationList, setApplicationList] = useState<ApplicationObject[]>();
  const [dataRetrievalList, setDataRetrievalList] = useState<ApplicationObject[]>();
  const [preProcessingList, setPreProcessingList] = useState<ApplicationObject[]>();
  const [isLoading, setIsLoading] = useState(true);
  const [hasError, setHasError] = useState(false);


  useEffect(() => {
    void (async () => {
      try {
        const data = await getApplicationList();
        setApplicationList(data);
        setIsLoading(false);
      } catch (error) {
        setIsLoading(false);
        setHasError(true);
        // eslint-disable-next-line no-console -- Current handling (consider a different error handling)
        console.error('Error fetching application list:', error);
      }
    })();
  }, []);

  useEffect(() => {
    if (applicationList) {
      setDataRetrievalList(applicationList.filter((app) => { return app.applicationType === ApplicationType.INGEST; }));
      setPreProcessingList(applicationList.filter((app) => { return app.applicationType === ApplicationType.PREPROCESS; }));
    }
  }, [applicationList]);

  

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
          <Section separator>Data Retrieval Applications</Section>
          {!dataRetrievalList ? null : 
            dataRetrievalList.length === 0 ?
              <Section>There are no data retrieval applications to display.</Section>
            :
            dataRetrievalList.map((app) => (
              <Card
                key={app.id}
                id={app.id}
                description={app.description}
                icon={app.icon}
                subtitle={`By ${app.creator}`}
                title={app.title}
                btnLabel="Open"
                url="/application"
              />
            ))
          }
          {!isLoading && !hasError ? null :
            <Section>{isLoading ?
              <div className="loading-box"><ElevaiteIcons.SVGSpinner/><span>Loading Applications. Please wait...</span></div> :
              <span>There has been an error loading the applications. Please try again later.</span>}
            </Section>
          }
          <Section separator>Preprocess Applications</Section>
          {!preProcessingList ? null : 
            preProcessingList.length === 0 ?
              <Section>There are no preprocessing applications to display.</Section>
            :
            preProcessingList.map((app) => (
              <Card
                key={app.id}
                id={app.id}
                description={app.description}
                icon={app.icon}
                subtitle={`By ${app.creator}`}
                title={app.title}
                btnLabel="Open"
                url="/application"
              />
            ))
          }
          {!isLoading && !hasError ? null :
            <Section>{isLoading ?
              <div className="loading-box"><ElevaiteIcons.SVGSpinner/><span>Loading Applications. Please wait...</span></div> :
              <span>There has been an error loading the applications. Please try again later.</span>}
            </Section>
          }
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
    </Tabs>
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
