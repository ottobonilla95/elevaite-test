"use client";
import { CommonButton, CommonSelect, ElevaiteIcons, type CommonSelectOption } from "@repo/ui/components";
import { useEffect, useState } from "react";
import { costBarChartAxisValues, useCost } from "../../../lib/contexts/CostContext";
import "./CostHeader.scss";


interface CostHeaderProps {
    isSidebarOpen: boolean;
    onSidebarToggle: () => void;
}


export function CostHeader(props: CostHeaderProps): JSX.Element {
    const costContext = useCost();
    const [totalDetails, setTotalDetails] = useState<{value: string; label: string; post: string}>({value: "—", label: "Total Cost", post: "$"});

    const showOptions: CommonSelectOption[] = [
        { value: costBarChartAxisValues.COST, label: "Cost" },
        { value: costBarChartAxisValues.TOKENS, label: "In & Out Tokens" },
        { value: costBarChartAxisValues.GPU, label: "GPU Usage" },
    ];


    useEffect(() => {
        const settingDetails = {label: "", value: "", post: ""};
        switch (costContext.costBarChartAxis) {
            case costBarChartAxisValues.COST: settingDetails.value = costContext.costDetails.totalCost?.toLocaleString(undefined, 
                { minimumFractionDigits: 2, maximumFractionDigits: 2 }) ?? "—"; settingDetails.label = "Total Cost"; settingDetails.post = "$"; break;
            case costBarChartAxisValues.GPU: settingDetails.value = costContext.costDetails.totalGpu?.toLocaleString(undefined, 
                { minimumFractionDigits: 0, maximumFractionDigits: 2 }) ?? "—"; settingDetails.label = "Total GPU Usage"; settingDetails.post = "mins"; break;
            case costBarChartAxisValues.TOKENS: settingDetails.value = costContext.costDetails.totalTokens?.toLocaleString(undefined, 
                { minimumFractionDigits: 0, maximumFractionDigits: 0 }) ?? "—"; settingDetails.label = "Total Tokens"; settingDetails.post = "tkn"; break;
        }
        setTotalDetails(settingDetails);
    }, [costContext.costBarChartAxis, costContext.costDetails]);



    function handleSidebarToggle(): void {
        props.onSidebarToggle();
    }

    function handleShowTypeChange(value: costBarChartAxisValues): void {
        costContext.setCostBarChartAxis(value);
    }


    return (
        <div className="cost-header-container">
            <div className="cost-header-title">
                <CommonButton
                    className={["cost-header-button", props.isSidebarOpen ? "open" : undefined].filter(Boolean).join(" ")}
                    onClick={handleSidebarToggle}
                >
                    <ElevaiteIcons.SVGSideArrow />
                </CommonButton>
                <span>Billing and Cost Management</span>
            </div>
            <div className="cost-header-info">
                <div className="primary info-block">                    
                    <div className="info-block-label">Cost & Usage Graph</div>
                    <div className="show-block">
                        <span className="show-label">Show:</span>
                        <CommonSelect
                            options={showOptions}
                            onSelectedValueChange={handleShowTypeChange}
                            defaultValue={costContext.costBarChartAxis}
                        />
                    </div>
                </div>
                <InfoBlock
                    label={totalDetails.label}
                    value={totalDetails.value}
                    post={totalDetails.post}
                />
                <InfoBlock
                    label="Model Count"
                    value={costContext.costDetails.uniqueModels?.length ?? "—"}
                    post={costContext.costDetails.uniqueModels?.length === 1 ? "Model" : "Models"}
                    valueTooltip={costContext.costDetails.uniqueModels?.join("\n")}
                />
                <InfoBlock
                    label="Project Count"
                    value={costContext.costDetails.uniqueProjects?.length ?? "—"}
                    post={costContext.costDetails.uniqueProjects?.length === 1 ? "Project" : "Projects"}
                    valueTooltip={costContext.costDetails.uniqueProjects?.join("\n")}
                />
            </div>
        </div>
    );
}




interface InfoBlockProps {
    label?: string;
    value?: string|number;
    post?: string;
    valueTooltip?: string;
}

function InfoBlock(props: InfoBlockProps): JSX.Element {
    return (
        <div className="info-block">
            <div className="info-block-label">{props.label}</div>
            <div className="info-block-value" title={props.valueTooltip}>
                <span className="value">{props.value}</span>
                <span className="value-post">{props.post}</span>
            </div>
        </div>
    )
}

