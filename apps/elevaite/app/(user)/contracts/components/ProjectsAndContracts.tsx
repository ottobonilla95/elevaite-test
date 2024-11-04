"use client";
import { useContracts } from "../../../lib/contexts/ContractsContext";
import { ContractsList } from "./ContractsList";
import { ContractsListV2 } from "./ContractsListV2";
import "./ProjectsAndContracts.scss";
import { ProjectsList } from "./ProjectsList";





export function ProjectsAndContracts(): JSX.Element {
    const contractsContext = useContracts();

    return (
        <div className={["contracts-content", !contractsContext.selectedContract ? "active" : undefined].filter(Boolean).join(" ")}>
            <div className="projects-and-contracts-container">
                <ProjectsList/>
                <ContractsListV2 />
            </div>
        </div>
    );
}