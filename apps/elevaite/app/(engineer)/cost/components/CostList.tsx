import "./CostList.scss";
import { CostListTable } from "./CostListTable";



export function CostList(): JSX.Element {
    return (
        <div className="cost-list-container">
            <div className="cost-list-table">
                <div className="cost-list-table-header-container">
                    <span>Cost & Usage Data</span>
                </div>
                <CostListTable/>
            </div>
        </div>
    );
}