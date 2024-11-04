import { useEffect, useState } from "react";
import { useContracts } from "../../../lib/contexts/ContractsContext";
import { CONTRACT_TYPES, ContractObject } from "../../../lib/interfaces";
import "./ComparisonSelect.scss";
import { CommonSelect, CommonSelectOption } from "@repo/ui/components";



interface ComparisonSelectProps {
    secondary?: boolean;
    listFor?: CONTRACT_TYPES;
}

export function ComparisonSelect(props: ComparisonSelectProps): JSX.Element {
    const contractsContext = useContracts();
    const [selectedContract, setSelectedContract] = useState<ContractObject|undefined>();
    const [contractOptions, setContractOptions] = useState<CommonSelectOption[]>([]);


    useEffect(() => {
        if (!props.secondary) setSelectedContract(contractsContext.selectedContract);
        else {
            if (contractsContext.secondarySelectedContract && typeof contractsContext.secondarySelectedContract === "object")
                setSelectedContract(contractsContext.secondarySelectedContract);
        }
        formatContractOptions(props.listFor);

    }, [props.listFor]);


    function handleSelection(value: string) {
        console.log("Selected", value);
        if (props.secondary) contractsContext.setSecondarySelectedContractById(value);
        else contractsContext.setSelectedContractById(value);
    }

    function formatContractOptions(type?: CONTRACT_TYPES): void {
        const options: CommonSelectOption[] = [];
        const contracts = contractsContext.selectedProject?.reports?.filter(report => !type ? report : report.content_type !== type);
        if (!contracts || contracts.length === 0) {            
            setContractOptions(options);
            return;
        }
        const vsow = contracts.filter(contract => contract.content_type === CONTRACT_TYPES.VSOW);
        if (vsow && vsow.length > 0) {
            options.push({value: "separatorVsow", label: "VSOW", isSeparator: true});
            options.push(...sortByLabelOrFileName(vsow).map(item => { return { value: item.id.toString(), label: item.label ?? item.filename, }; } ));
        }
        const csow = contracts.filter(contract => contract.content_type === CONTRACT_TYPES.CSOW);
        if (csow && csow.length > 0) {
            options.push({value: "separatorCsow", label: "CSOW", isSeparator: true});
            options.push(...sortByLabelOrFileName(csow).map(item => { return { value: item.id.toString(), label: item.label ?? item.filename, }; } ));
        }
        const po = contracts.filter(contract => contract.content_type === CONTRACT_TYPES.PURCHASE_ORDER);
        if (po && po.length > 0) {
            options.push({value: "separatorPo", label: "PO", isSeparator: true});
            options.push(...sortByLabelOrFileName(po).map(item => { return { value: item.id.toString(), label: item.label ?? item.filename, }; } ));
        }
        const invoice = contracts.filter(contract => contract.content_type === CONTRACT_TYPES.INVOICE);
        if (invoice && invoice.length > 0) {
            options.push({value: "separatorInvoice", label: "Invoices", isSeparator: true});
            options.push(...sortByLabelOrFileName(invoice).map(item => { return { value: item.id.toString(), label: item.label ?? item.filename, }; } ));
        }

        setContractOptions(options);
        
        function sortByLabelOrFileName(list: ContractObject[]): ContractObject[] {
            list.sort((a, b) => {
                const valueA = a.label ?? a.filename;
                const valueB = b.label ?? b.filename;
                return valueA.localeCompare(valueB);
            })
            return list;
        }
    }



    return (
        <div className="comparison-select-container">
            <CommonSelect
                options={contractOptions}
                onSelectedValueChange={handleSelection}
                controlledValue={selectedContract?.id.toString() ?? ""}
                showTitles
                showSelected
            />
        </div>
    );
}