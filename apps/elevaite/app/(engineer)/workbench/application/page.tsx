"use client"
import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { CommonModal } from "@repo/ui/components";
import { ApplicationObject, type AppInstanceObject } from "../../../lib/interfaces";
import AppInstanceList from "./AppInstanceList";
import ApplicationDetails from "./ApplicationDetails";
import WidgetDocker from "./WidgetDocker";
import "./page.scss";
import { AddInstanceForm } from "./addInstance/AddInstanceForm";
import { getApplicationById, getApplicationInstanceList, getApplicationPipelines } from "../../../lib/actions";
import { S3DataRetrievalAppInstanceForm } from "../../../lib/dataRetrievalApps";
import { S3PreprocessingAppInstanceForm } from "../../../lib/preprocessingApps";



export default function Page(): JSX.Element {
  const searchParams = useSearchParams();
  const id = searchParams.get('id');
  const router = useRouter();
  const [isDetailsLoading, setIsDetailsLoading] = useState(true);
  const [hasError, setHasError] = useState(false);
  const [applicationDetails, setApplicationDetails] = useState<ApplicationObject|undefined>();
  const [appInstanceList, setAppInstanceList] = useState<AppInstanceObject[]|undefined>();
  const [selectedInstance, setSelectedInstance] = useState<AppInstanceObject>();
  const [isAddInstanceModalOpen, setIsAddInstanceModalOpen] = useState(false);
  const [selectedFlow, setSelectedFlow] = useState<string>("documents");


  useEffect(() => {
    void (async () => {
      try {
        if (!id) return;
        setIsDetailsLoading(true);
        const data = await getApplicationById(id);
        setApplicationDetails(data);
        setIsDetailsLoading(false);
      } catch (error) {
        setIsDetailsLoading(false);
        setHasError(true);
        console.error('Error fetching application list', error);
      }
    })();
    // void (async () => {
    //   try {
    //     if (!id) return;
    //     const pipelines = await getApplicationPipelines(id);
    //     console.log("Pipelines:", pipelines);
    //   } catch (error) {
    //     setHasError(true);
    //     console.error('Error fetching application pipelines', error);
    //   }
    // })();
  }, [id]);


  function getAddInstanceStructure(id: string|null) {
    switch (id) {
      case "1": return S3DataRetrievalAppInstanceForm;
      case "2": return S3PreprocessingAppInstanceForm;
      default: return undefined;
    }
  }


  function handleAddInstanceClose(refresh?: boolean) {
    //TODO: If refresh
    setIsAddInstanceModalOpen(false);
  }

  
  function onBack(): void {
    router.back();
  }

  function handleSelectedInstanceChange(instance: AppInstanceObject|undefined): void {
    setSelectedInstance(instance);
  }

  function handleSelectedFlowChange(flow: string): void {
    setSelectedFlow(flow);
  }


  return (
    <div className="ingest-container">

      <div className="details-container">
        <ApplicationDetails
          applicationDetails={applicationDetails}
          isLoading={isDetailsLoading}
          onBack={onBack}
        />
      </div>

      <div className="instances-container">
        <AppInstanceList
          applicationId={id}
          applicationType={applicationDetails?.applicationType}
          onAddInstanceClick={() => {setIsAddInstanceModalOpen(true)}}
          onSelectedInstanceChange={handleSelectedInstanceChange}
          onSelectedFlowChange={handleSelectedFlowChange}
        />
      </div>

      <div className="widgets-container">
        <WidgetDocker
          applicationId={id}
          applicationType={applicationDetails?.applicationType}
          selectedInstance={selectedInstance}
          selectedFlow={selectedFlow}
        />
      </div>

      {!isAddInstanceModalOpen ? null :
        <CommonModal onClose={handleAddInstanceClose}>
          <AddInstanceForm
            applicationId={id}
            addInstanceStructure={getAddInstanceStructure(id)}
            onClose={handleAddInstanceClose}
          />
        </CommonModal>
      }
    </div>
  );
}






