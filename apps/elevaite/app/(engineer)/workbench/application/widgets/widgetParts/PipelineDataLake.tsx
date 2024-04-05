"use client";
import { ElevaiteIcons, SimpleInput } from "@repo/ui/components";
import { useState } from "react";
import "./PipelineDataLake.scss";



interface PipelineDataLakeProps {
    totalFiles: number;
    doc?: number;
    zip?: number;
}

export function PipelineDataLake(props: PipelineDataLakeProps): JSX.Element {
    const [searchTerm, setSearchTerm] = useState("");


    return (
        <div className="pipeline-datalake-container">
            <span className="title">Data Lake</span>

            {/* <div className="file-info-container">
                <div className="file-info">{props.totalFiles} Total Files</div>
                {!props.doc ? undefined : 
                    <div className="file-info"><span>{props.doc}</span><span className="type">.docx</span></div>
                }
                {!props.zip ? undefined :
                    <div className="file-info"><span>{props.zip}</span><span className="type">.zip</span></div>
                }
            </div> */}

            <div className="search-container">
                <ElevaiteIcons.SVGMagnifyingGlass/>
                <SimpleInput
                    value={searchTerm}
                    onChange={setSearchTerm}
                    placeholder="Search document by name"
                />
            </div>

            <div className="upload-container">
                <div className="icon-container">
                    <ElevaiteIcons.SVGCloudUpload/>
                </div>
                <span className="green">Click to Upload File</span>
                <span>or drag and drop your file here</span>
            </div>
        </div>
    );
}