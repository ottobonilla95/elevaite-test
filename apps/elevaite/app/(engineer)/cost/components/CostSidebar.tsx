import { CommonFormLabels, CommonSelect, SimpleInput, type CommonSelectOption } from "@repo/ui/components";
import { useEffect, useState } from "react";
import { useCost } from "../../../lib/contexts/CostContext";
import "./CostSidebar.scss";


const DEFAULT_ACCOUNTS_VALUE = "All";



export function CostSidebar(): JSX.Element {
    const costContext = useCost();
    const [accountOptions, setAccountOptions] = useState<CommonSelectOption[]>([]);

    useEffect(() => {
        if (!costContext.costDetails.uniqueAccounts) return;

        const formattedAccounts = costContext.costDetails.uniqueAccounts.map(item => { return {
            value: item,
        }; });
        formattedAccounts.unshift({value: DEFAULT_ACCOUNTS_VALUE});
        setAccountOptions(formattedAccounts);
    }, [costContext.costDetails]);

    // useEffect(() => {
    //     console.log("account options:", accountOptions);        
    // }, [accountOptions]);


    function handleAccountChange(value: string): void {
        costContext.filterByAccount(value);
    }



    return (
        <div className="cost-sidebar-container">
            <div className="parameters-container">
                <span>Parameters</span>
                <CommonFormLabels
                    className="parameter-item"
                    label="Account"
                >
                    <CommonSelect
                        options={accountOptions}
                        onSelectedValueChange={handleAccountChange}
                        defaultValue={DEFAULT_ACCOUNTS_VALUE}
                        callbackOnDefaultValue
                    />
                </CommonFormLabels>
                <CommonFormLabels
                    className="parameter-item"
                    label="Month"
                >
                    <SimpleInput
                        value="May 2024"
                        onChange={() => {/** */}}
                    />
                </CommonFormLabels>
            </div>
            {/* <div className="filters-container">
                <span>Additional Filters</span>
            </div> */}
        </div>
    );
}