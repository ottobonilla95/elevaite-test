import { CommonInput, ElevaiteIcons } from "@repo/ui/components";
import { useEffect, useState } from "react";
import { type ContractObject, type ContractObjectEmphasis, } from "../../../interfaces";
import "./PdfExtractionEmphasis.scss";

interface PdfExtractionEmphasisProps {
  selectedContract?: ContractObject;
  secondary?: boolean;
  borderless?: boolean;
}

export function PdfExtractionEmphasis(props: PdfExtractionEmphasisProps): React.ReactNode {
  const [emphasisData, setEmphasisData] = useState<ContractObjectEmphasis | null>();



  useEffect(() => {
    setEmphasisData(props.selectedContract?.highlight);
  }, [props.selectedContract]);



  return !props.selectedContract && !props.secondary ? (
    <div className={["pdf-extraction-emphasis-container", props.borderless ? "borderless" : undefined].filter(Boolean).join(" ")}>
      <div className="loading">
        <ElevaiteIcons.SVGSpinner />
      </div>
    </div>
  ) : !emphasisData ? undefined : (
    <div className={["pdf-extraction-emphasis-container", props.borderless ? "borderless" : undefined].filter(Boolean).join(" ")}>
      <div className="pdf-emphasis-block">
        <EmphasisBit emphasisData={emphasisData} label="PO Number" valueKey="po_number" />
        <EmphasisBit emphasisData={emphasisData} label="Customer PO Number" valueKey="customer_po_number" />
        <EmphasisBit emphasisData={emphasisData} label="Customer Name" valueKey="customer_name" />
        <EmphasisBit emphasisData={emphasisData} label="Invoice Number" valueKey="invoice_number" />
        <EmphasisBit emphasisData={emphasisData} label="Supplier" valueKey="supplier" />
      </div>
      {(!emphasisData.po_number &&
        !emphasisData.invoice_number &&
        !emphasisData.supplier) ||
        (!emphasisData.non_rec_charges &&
          !emphasisData.rec_charges &&
          !emphasisData.total_amount) ? undefined : (
        <div className="separator" />
      )}
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
  return !value || typeof value !== "string" ? undefined : (
    <CommonInput
      label={props.label}
      controlledValue={value}
      disabled
      noDisabledTooltip
    />
  );
}
