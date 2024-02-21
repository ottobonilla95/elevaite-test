"use client"
import type { CommonSelectOption } from "@repo/ui/components";
import { CommonModal } from "@repo/ui/components";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";
import { getApplicationById, getApplicationPipelines } from "../../../lib/actions";
import { S3DataRetrievalAppInstanceForm } from "../../../lib/dataRetrievalApps";
import type { AppInstanceFormStructure, AppInstanceObject, ApplicationObject, Initializers, PipelineObject } from "../../../lib/interfaces";
import { S3PreprocessingAppInstanceForm } from "../../../lib/preprocessingApps";
import AppInstanceList from "./AppInstanceList";
import ApplicationDetails from "./ApplicationDetails";
import WidgetDocker from "./WidgetDocker";
import { AddInstanceForm } from "./addInstance/AddInstanceForm";
import "./page.scss";



export default function Page(): JSX.Element {
  const searchParams = useSearchParams();
  const id = searchParams.get('id');
  const router = useRouter();
  const [formStructure, setFormStructure] = useState<AppInstanceFormStructure<Initializers>>();
  const [isDetailsLoading, setIsDetailsLoading] = useState(true);
  // const [hasError, setHasError] = useState(false);
  const [applicationDetails, setApplicationDetails] = useState<ApplicationObject|undefined>();
  const [selectedInstance, setSelectedInstance] = useState<AppInstanceObject>();
  const [isAddInstanceModalOpen, setIsAddInstanceModalOpen] = useState(false);
  const [selectedFlow, setSelectedFlow] = useState<CommonSelectOption>();
  const [pipelines, setPipelines] = useState<PipelineObject[]>([]);
  const [addId, setAddId] = useState("");


  useEffect(() => {
    assignStructure(id);
    void (async () => {
      try {
        if (!id) return;
        setIsDetailsLoading(true);
        const data = await getApplicationById(id);
        setApplicationDetails(data);
        setIsDetailsLoading(false);
      } catch (error) {
        setIsDetailsLoading(false);
        // setHasError(true);
        // eslint-disable-next-line no-console -- Current handling (consider a different error handling)
        console.error('Error fetching application list', error);
      }
    })();
    void (async () => {
      try {
        if (!id) return;
        const fetchedPipelines = await getApplicationPipelines(id);
        if (fetchedPipelines.length === 0) return;
        setPipelines(fetchedPipelines);
      } catch (error) {
        // setHasError(true);
        // eslint-disable-next-line no-console -- Current handling (consider a different error handling)
        console.error('Error fetching application pipelines', error);
      }
    })();
  }, [id]);


  function assignStructure(assignedId: string|null): void {
    if (!assignedId) return;
    switch (assignedId) {
      case "1": setFormStructure(S3DataRetrievalAppInstanceForm); break;
      case "2": setFormStructure(S3PreprocessingAppInstanceForm); break;
    }
  }


  function handleAddInstanceClose(addingId?: string): void {
    if (addingId) setAddId(addingId);
    setIsAddInstanceModalOpen(false);
  }

  
  function onBack(): void {
    router.back();
  }

  function handleSelectedInstanceChange(instance: AppInstanceObject|undefined): void {
    setSelectedInstance(instance);
  }

  function handleSelectedFlowChange(flowValue: string, flowLabel: string): void {
    setSelectedFlow({
      label: flowLabel,
      value: flowValue,
    });
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
          pipelines={pipelines}
          onAddInstanceClick={() => {setIsAddInstanceModalOpen(true)}}
          onSelectedInstanceChange={handleSelectedInstanceChange}
          onSelectedFlowChange={handleSelectedFlowChange}
          addId={addId}
          onClearAddId={(passedId) => { setAddId((currentId) => passedId === currentId ? "" : currentId ); }}
        />
      </div>

      <div className="widgets-container">
        <WidgetDocker
          applicationId={id}
          applicationDetails={applicationDetails}
          selectedInstance={selectedInstance}
          selectedFlow={selectedFlow}
          pipelines={pipelines}
        />
      </div>

      {!isAddInstanceModalOpen ? null :
        <CommonModal onClose={handleAddInstanceClose}>
          <AddInstanceForm
            applicationId={id}
            addInstanceStructure={formStructure}
            selectedFlow={selectedFlow}
            onClose={handleAddInstanceClose}
          />
        </CommonModal>
      }
    </div>
  );
}






