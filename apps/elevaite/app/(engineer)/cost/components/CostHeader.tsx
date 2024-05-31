import { CommonButton, CommonSelect, ElevaiteIcons, type CommonSelectOption } from "@repo/ui/components";
import { useCost } from "../../../lib/contexts/CostContext";
import "./CostHeader.scss";


interface CostHeaderProps {
    isSidebarOpen: boolean;
    onSidebarToggle: () => void;
}


export function CostHeader(props: CostHeaderProps): JSX.Element {
    const costContext = useCost();

    const showOptions: CommonSelectOption[] = [
        { value: "cost", label: "Cost" },
        { value: "tokens", label: "In & Out Tokens" },
        { value: "gpu", label: "GPU Usage" },
    ];

    function handleSidebarToggle(): void {
        props.onSidebarToggle();
    }

    function handleSelectChange(value: string, label: string): void {
        console.log("Changed view:", label);
    }


    return (
        <div className="cost-header-container">
            <div className="cost-header-title">
                <CommonButton
                    className={["cost-header-button", props.isSidebarOpen ? "open" : undefined].filter(Boolean).join(" ")}
                    onClick={handleSidebarToggle}
                >
                    <ElevaiteIcons.SVGChevron type="right" />
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
                            onSelectedValueChange={handleSelectChange}
                            defaultValue={showOptions[0].value}
                        />
                    </div>
                </div>
                <InfoBlock
                    label="Total Cost"
                    value={costContext.costDetails.formattedCost ?? "—"}
                    post="$"
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

