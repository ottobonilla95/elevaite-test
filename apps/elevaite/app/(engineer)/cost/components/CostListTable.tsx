import { specialHandlingCostFields, useCost } from "../../../lib/contexts/CostContext";
import { CostListRow, type RowStructure } from "./CostListRow";
import "./CostListTable.scss";





export function CostListTable(): JSX.Element {
    const costContext = useCost();
   
    const costListStructure: RowStructure[] = [
        { header: "Account", field: "account", isSortable: true, ellipses: true, },
        { header: "Project", field: "project", isSortable: true, ellipses: true, },
        { header: "Model Provider", field: "modelProvider", isSortable: true, ellipses: true, },
        { header: "Model", field: "modelId", isSortable: true, ellipses: true, specialHandling: specialHandlingCostFields.MODEL },
        { header: "Inference Date", field: "inferenceDate", isSortable: true, align: "center", style: "block", specialHandling: specialHandlingCostFields.DATE },
        { header: "Inference Count", field: "inferenceCount", isSortable: true, align: "center", style: "block", specialHandling: specialHandlingCostFields.AMOUNT },
        { header: "Billing", field: "billingType", isSortable: true, align: "center", specialHandling: specialHandlingCostFields.TAGS },
        { header: "Tokens In", field: "tokensIn", isSortable: true, align: "center", style: "block", specialHandling: specialHandlingCostFields.AMOUNT },
        { header: "Tokens Out", field: "tokensOut", isSortable: true, align: "center", style: "block", specialHandling: specialHandlingCostFields.AMOUNT },
        { header: "GPU Usage", field: "gpu", isSortable: true, subtitle: "(In mins)", align: "right", specialHandling: specialHandlingCostFields.FRACTION_AMOUNT },
        { header: "Latency", field: "latency", isSortable: true, subtitle: "(Avg in ms)", align: "right", specialHandling: specialHandlingCostFields.AMOUNT },
        { header: "Cost", field: "cost", isSortable: true, align: "right", specialHandling: specialHandlingCostFields.PRICE },
        // inferenceHour is unused
    ];


    return (
        <div className="cost-list-table-container">
                <div className="cost-list-table-grid">
                    <CostListRow isHeader structure={costListStructure} />
                    {costContext.costData.length === 0 ? 
                        <div className="table-span empty">
                            There is no cost data to display.
                        </div>

                    :

                    costContext.costData.map((cost) => 
                        <CostListRow
                            key={cost.id}
                            cost={cost}
                            structure={costListStructure}
                        />
                    )}
                </div>
        </div>
    );
}