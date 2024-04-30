import { ElevaiteIcons } from "@repo/ui/components";
import { useEffect, useState } from "react";
import { S3DataRetrievalAppInstanceForm } from "../../../../../lib/dataRetrievalApps";
import { getConfigurationObjectFromRaw } from "../../../../../lib/helpers";
import type { AppInstanceConfigurationObject, AppInstanceFieldStructure, AppInstanceFormStructure, Initializers } from "../../../../../lib/interfaces";
import { AppInstanceFieldTypes, ApplicationType } from "../../../../../lib/interfaces";
import "./PipelineInfoConfiguration.scss";
import { S3PreprocessingAppInstanceForm } from "../../../../../lib/preprocessingApps";




interface PipelineInfoConfigurationProps {
    isSkeleton?: boolean;
    type?: ApplicationType;
    configuration?: AppInstanceConfigurationObject;
}

export function PipelineInfoConfiguration(props: PipelineInfoConfigurationProps): JSX.Element {
    const [configStructure, setConfigStructure] = useState<AppInstanceFormStructure<Initializers>|undefined>();


    useEffect(() => {
        if (props.isSkeleton) return;
        if (props.type === ApplicationType.INGEST) {
            setConfigStructure(S3DataRetrievalAppInstanceForm);
        } else if (props.type === ApplicationType.PREPROCESS) {
            setConfigStructure(S3PreprocessingAppInstanceForm);
        }
    }, [props.type, props.configuration, props.isSkeleton]);



    
    function mapFields(fields: AppInstanceFieldStructure[]): JSX.Element {
        const configValues = getConfigurationObjectFromRaw(props.configuration?.raw);


        const components = fields.map((field) => {            
            if (!("type" in field)) return null;
            if (field.type === AppInstanceFieldTypes.GROUP) {
                return (
                    <ConfigGroupContainer
                        key={`group_${field.label}`}
                        title={field.label}
                    >
                        {mapFields(field.fields)}
                    </ConfigGroupContainer>
                )
            } else if (field.type === AppInstanceFieldTypes.CHECKBOX) {
                return  <ConfigBlockCheckbox
                            key={`checkbox_${field.label ?? ""}`}
                            label={field.label ? field.label : ""}
                            value={field.field && configValues?.[field.field] ? configValues[field.field] as boolean : undefined}
                        />
            } 
            return  <ConfigBlock
                        key={`block_${field.label ?? ""}`}
                        label={field.label ? field.label : ""}
                        value={field.field && configValues?.[field.field] ? configValues[field.field] as string : undefined}
                        info={field.info ? field.info : ""}
                    />              
        });
        return <>{components}</>;
    }




    return (
        <div className="pipeline-info-configuration-container">
            {configStructure && !props.isSkeleton ?
                mapFields(configStructure.fields)
                :
                <SkeletonBlock/>
            }
        </div>
    );
}





function ConfigBlock(props: {label: string, value?: string, info?: string;}): JSX.Element {
    return (
        <div className="info-config-block">
            <div className="info-config-label">
                <span>{props.label}</span>
                {!props.info ? null : 
                    <div className="info-config-icon" title={props.info}><ElevaiteIcons.SVGInfo/></div>
                }
            </div>
            <div className="info-config-value">{props.value ? props.value : "\u200B"}</div>
        </div>
    );
}

function ConfigBlockCheckbox(props: {label: string, value?: boolean, info?: string;}): JSX.Element {
    return (
        <div className="info-config-block">
            <div className="info-config-label">
                <div className="info-config-checkbox">
                    {props.value ? <ElevaiteIcons.SVGCheckmark/> : null}
                </div>
                <span>{props.label}</span>
                {!props.info ? null : 
                    <div className="info-config-icon" title={props.info}><ElevaiteIcons.SVGInfo/></div>
                }
            </div>
        </div>
    );
}

function ConfigGroupContainer(props: {title: string; children: React.ReactNode}): JSX.Element {
    return (
        <div className="info-config-group-container">
            <div className="config-group-title">{props.title}</div>
            {props.children}
        </div>
    );
}



function SkeletonBlock(): JSX.Element {
    const skeletonParts = [0, 1, 2, 3, 4, 5];
    return (
        <>
            {skeletonParts.map(item => 
                <div className="info-config-block" key={item}>
                    <div className="info-config-label skeleton"/>
                    <div className="info-config-value skeleton"/>
                </div>
            )}
        </>
    );
}

