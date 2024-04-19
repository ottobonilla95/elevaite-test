"use client";
import { ElevaiteIcons, type CommonMenuItem } from "@repo/ui/components";
import { useEffect, useState } from "react";
import { specialHandlingDatasetFields, useDatasets } from "../../../../lib/contexts/DatasetsContext";
import { type ModelDatasetObject } from "../../../../lib/interfaces";
import { DatasetsListRow, type RowStructure } from "./DatasetsListRow";
import "./DatasetsListTable.scss";



enum MENU_ACTIONS {
    DOWNLOAD = "Download",
};


interface DatasetsListTableProps {
    isVisible?: boolean;
}

export function DatasetsListTable(props: DatasetsListTableProps): JSX.Element {
    const datasetContext = useDatasets();
    const [displayDatasets, setDisplayDatasets] = useState<ModelDatasetObject[]>([]);


    
    const datasetsListStructure: RowStructure[] = [
        { header: "Dataset Name", field: "name", isSortable: true },
        { header: "Dataset Description", field: "huggingface_repo", isSortable: true },
        { header: "Dataset Id", field: "id", isSortable: false },
        { header: "Task", field: "task", isSortable: true },
        { header: "Rows", field: "rows", isSortable: true, align: "center", style: "block" },
        { header: "Columns", field: "columns", isSortable: true, align: "center", style: "block" },
        { header: "Tags", field: "tags", isSortable: true, specialHandling: specialHandlingDatasetFields.TAGS },
        { header: "Download Size", field: "size", isSortable: true },
        { header: "Registered at", field: "created", isSortable: true, specialHandling: specialHandlingDatasetFields.DATE, align: "right" },
    ];


    const datasetsListMenu: CommonMenuItem<ModelDatasetObject>[] = [
        { label: "Download Dataset", onClick: (item: ModelDatasetObject) => { handleMenuClick(item, MENU_ACTIONS.DOWNLOAD); } },
    ]


    useEffect(() => {
        setDisplayDatasets(datasetContext.datasets);
    }, [datasetContext.datasets]);




    function handleMenuClick(dataset: ModelDatasetObject, action: MENU_ACTIONS): void {
        switch (action) {
            case MENU_ACTIONS.DOWNLOAD: console.log("Clicked download"); break;
            default: break;
        }
    }



    return (
        <div className={[
            "datasets-list-table-container",
            props.isVisible ? "is-visible" : undefined,
        ].filter(Boolean).join(" ")}>
            {datasetContext.loading.datasets ? 
                <div className="table-span">
                    <ElevaiteIcons.SVGSpinner/>
                    <span>Loading...</span>
                </div>
            :            
            
                <div className="datasets-list-table-grid">
                    <DatasetsListRow isHeader structure={datasetsListStructure} menu={datasetsListMenu} />
                    {displayDatasets.length === 0 ? 
                        <div className="table-span empty">
                            There are no datasets to display.
                        </div>

                    :

                    displayDatasets.map((dataset, index) => 
                        <DatasetsListRow
                            key={dataset.id}
                            dataset={dataset}
                            structure={datasetsListStructure}
                            menu={datasetsListMenu}
                            menuToTop={displayDatasets.length > 4 && index > (displayDatasets.length - 4) }
                        />
                    )}
                </div>
            }


        </div>
    );
}