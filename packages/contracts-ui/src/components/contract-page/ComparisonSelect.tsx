import { useEffect, useState } from "react";
import { CommonSelect, type CommonSelectOption } from "@repo/ui/components";
import { CONTRACT_TYPES, type ContractObject } from "@/interfaces";
import "./ComparisonSelect.scss";

interface ComparisonSelectProps {
  secondary?: boolean;
  listFor?: CONTRACT_TYPES;
  selectedContract?: ContractObject;
  selectedProject?: { reports?: ContractObject[] };
  secondarySelectedContract?: ContractObject | CONTRACT_TYPES;
  setSelectedContract: (contract?: ContractObject) => void;
  setSecondarySelectedContractById: (id: string) => void;
  setSelectedContractById: (id: string) => void;
}

export function ComparisonSelect(props: ComparisonSelectProps): JSX.Element {
  const [contractOptions, setContractOptions] = useState<CommonSelectOption[]>(
    []
  );

  useEffect(() => {
    function formatContractOptions(type?: CONTRACT_TYPES): void {
      const options: CommonSelectOption[] = [];
      const contracts = props.selectedProject?.reports?.filter((report) =>
        !type ? report : report?.content_type !== type
      );

      if (!contracts || contracts.length === 0) {
        setContractOptions(options);
        return;
      }
      const vsow = contracts.filter(
        (contract) => contract.content_type === CONTRACT_TYPES.VSOW
      );
      if (vsow.length > 0) {
        options.push({
          value: "separatorVsow",
          label: "VSOW",
          isSeparator: true,
        });
        options.push(
          ...sortByLabelOrFileName(vsow).map((item) => {
            return {
              value: item.id.toString(),
              label: item.label ?? item.filename,
            };
          })
        );
      }
      const csow = contracts.filter(
        (contract) => contract.content_type === CONTRACT_TYPES.CSOW
      );
      if (csow.length > 0) {
        options.push({
          value: "separatorCsow",
          label: "CSOW",
          isSeparator: true,
        });
        options.push(
          ...sortByLabelOrFileName(csow).map((item) => {
            return {
              value: item.id.toString(),
              label: item.label ?? item.filename,
            };
          })
        );
      }
      const po = contracts.filter(
        (contract) => contract.content_type === CONTRACT_TYPES.PURCHASE_ORDER
      );
      if (po.length > 0) {
        options.push({
          value: "separatorPo",
          label: "PO",
          isSeparator: true,
        });
        options.push(
          ...sortByLabelOrFileName(po).map((item) => {
            return {
              value: item.id.toString(),
              label: item.label ?? item.filename,
            };
          })
        );
      }
      const invoice = contracts.filter(
        (contract) => contract.content_type === CONTRACT_TYPES.INVOICE
      );
      if (invoice.length > 0) {
        options.push({
          value: "separatorInvoice",
          label: "Invoices",
          isSeparator: true,
        });
        options.push(
          ...sortByLabelOrFileName(invoice).map((item) => {
            return {
              value: item.id.toString(),
              label: item.label ?? item.filename,
            };
          })
        );
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

    if (!props.secondary) props.setSelectedContract(props.selectedContract);
    else if (
      props.secondarySelectedContract &&
      typeof props.secondarySelectedContract === "object"
    )
      props.setSelectedContract(props.secondarySelectedContract);
    formatContractOptions(props.listFor);
  }, [contractOptions, props, props.listFor]);

  function handleSelection(value: string): void {
    if (props.secondary) props.setSecondarySelectedContractById(value);
    else props.setSelectedContractById(value);
  }

  return (
    <div className="comparison-select-container">
      <CommonSelect
        options={contractOptions}
        onSelectedValueChange={handleSelection}
        controlledValue={
          props.selectedContract ? props.selectedContract.id.toString() : ""
        }
        showTitles
        showSelected
      />
    </div>
  );
}
