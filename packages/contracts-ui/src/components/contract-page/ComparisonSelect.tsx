import { useEffect, useState } from "react";
import { CommonSelect, type CommonSelectOption } from "@repo/ui/components";
import { useRouter } from "next/navigation";
import { CONTRACT_TYPES, type ContractObject } from "../../interfaces";
import "./ComparisonSelect.scss";




interface ComparisonSelectProps {
  secondary?: boolean;
  listFor?: CONTRACT_TYPES;
  contractId: string;
  comparedContractId?: string;
  projectId: string;
  contractsList: ContractObject[];
}

export function ComparisonSelect(props: ComparisonSelectProps): JSX.Element {
  const router = useRouter();
  const [contractOptions, setContractOptions] = useState<CommonSelectOption[]>([]);


  useEffect(() => {
    formatContractOptions(props.listFor);
  }, [props.listFor]);



  function handleSelection(value: string): void {
    if (value.toLowerCase().includes("separator")) return;
    if (props.secondary) {
      if (value === props.comparedContractId) return;
      router.push(`/${props.projectId}/${props.contractId}/compare/${value}`);
    } else {
      if (value === props.contractId) return;
      router.push(`/${[props.projectId, value, "compare", props.comparedContractId ?? undefined].filter(Boolean).join("/")}`)
    }
  }




  function formatContractOptions(type?: CONTRACT_TYPES): void {
    const options: CommonSelectOption[] = [];
    const contracts = props.contractsList.filter((report) => !type ? report : report.content_type !== type);
    if (contracts.length === 0) {
      setContractOptions(options);
      return;
    }
    const vsow = contracts.filter(contract => contract.content_type === CONTRACT_TYPES.VSOW);
    if (vsow.length > 0) {
        options.push({value: "separatorVsow", label: "VSOW", isSeparator: true});
        options.push(...sortByLabelOrFileName(vsow).map(item => { return { value: item.id.toString(), label: item.label ?? item.filename, }; } ));
    }
    const csow = contracts.filter(contract => contract.content_type === CONTRACT_TYPES.CSOW);
    if (csow.length > 0) {
        options.push({value: "separatorCsow", label: "CSOW", isSeparator: true});
        options.push(...sortByLabelOrFileName(csow).map(item => { return { value: item.id.toString(), label: item.label ?? item.filename, }; } ));
    }
    const po = contracts.filter(contract => contract.content_type === CONTRACT_TYPES.PURCHASE_ORDER);
    if (po.length > 0) {
        options.push({value: "separatorPo", label: "PO", isSeparator: true});
        options.push(...sortByLabelOrFileName(po).map(item => { return { value: item.id.toString(), label: item.label ?? item.filename, }; } ));
    }
    const invoice = contracts.filter(contract => contract.content_type === CONTRACT_TYPES.INVOICE);
    if (invoice.length > 0) {
        options.push({value: "separatorInvoice", label: "Invoices", isSeparator: true});
        options.push(...sortByLabelOrFileName(invoice).map(item => { return { value: item.id.toString(), label: item.label ?? item.filename, }; } ));
    }

    setContractOptions(options);

    function sortByLabelOrFileName(list: ContractObject[]): ContractObject[] {
      list.sort((a, b) => {
        const valueA = a.label ?? a.filename;
        const valueB = b.label ?? b.filename;
        return valueA.localeCompare(valueB);
      });
      return list;
    }
  }
  

  return (
    <div className="comparison-select-container">
      <CommonSelect
        options={contractOptions}
        onSelectedValueChange={handleSelection}
        controlledValue={props.secondary ? (props.comparedContractId ?? undefined) : props.contractId}
        showTitles
        showSelected
        noSelectionMessage="Select a file to compare with"
      />
    </div>
  );
}
