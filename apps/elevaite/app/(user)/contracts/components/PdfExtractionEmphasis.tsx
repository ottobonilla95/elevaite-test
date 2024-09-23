import { CommonInput } from "@repo/ui/components";
import { useEffect, useState } from "react";
import { useContracts } from "../../../lib/contexts/ContractsContext";
import { type ContractObjectEmphasis } from "../../../lib/interfaces";
import "./PdfExtractionEmphasis.scss";




export function PdfExtractionEmphasis(): React.ReactNode {
    const contractsContext = useContracts();
    const [emphasisData, setEmphasisData] = useState<ContractObjectEmphasis>();

    useEffect(() => {
        setEmphasisData(contractsContext.selectedContract?.highlight);
    }, [contractsContext.selectedContract]);

    return (
        !emphasisData ? undefined :
        <div className="pdf-extraction-emphasis-container">
            <div className="pdf-emphasis-block">
                <EmphasisBit emphasisData={emphasisData} label="PO Number" valueKey="po_number" />
                <EmphasisBit emphasisData={emphasisData} label="Invoice Number" valueKey="invoice_number" />
                <EmphasisBit emphasisData={emphasisData} label="Supplier" valueKey="supplier" />
            </div>
            {(!emphasisData.po_number && !emphasisData.invoice_number && !emphasisData.supplier)
                || (!emphasisData.non_rec_charges && !emphasisData.rec_charges && !emphasisData.total_amount) ? undefined :
                <div className="separator"/>
            }
            <div className="pdf-emphasis-block">
                <EmphasisBit emphasisData={emphasisData} label="Recurring Charges" valueKey="rec_charges" />
                <EmphasisBit emphasisData={emphasisData} label="Non-recurring Charges" valueKey="non_rec_charges" />
                <EmphasisBit emphasisData={emphasisData} label="Total Amount" valueKey="total_amount" />
            </div>
        </div>
    );
}



interface EmphasisBitProps {
    emphasisData: ContractObjectEmphasis;
    valueKey: keyof ContractObjectEmphasis;
    label: string;
}

function EmphasisBit(props: EmphasisBitProps): React.ReactNode {
    const value = props.emphasisData[props.valueKey];
    return (
        !value || typeof value !== "string" ? undefined :
        <CommonInput
            label={props.label}
            initialValue={value}
            disabled
            noDisabledTooltip
        />
    );
}

