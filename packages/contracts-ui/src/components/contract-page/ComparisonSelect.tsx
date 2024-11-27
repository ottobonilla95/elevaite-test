import { useEffect, useState } from "react";
import { CommonSelect, type CommonSelectOption } from "@repo/ui/components";
import { useRouter } from "next/navigation";
import { CONTRACT_TYPES, type ContractObject } from "../../interfaces";
import "./ComparisonSelect.scss";

function useHandleSelection(
  secondary: boolean | undefined,
  projectId: string,
  primaryContractId: string | number | undefined,
  secondaryContractId: string | number | undefined
) {
  const router = useRouter();

  // eslint-disable-next-line @typescript-eslint/no-unused-vars -- Wrapper function
  return (value: string, label: string) => {
    if (isNaN(Number(value))) {
      return;
    }

    if (secondary && primaryContractId && primaryContractId !== value) {
      router.push(`/${projectId}/${primaryContractId}/compare/${value}`);
    } else if (secondaryContractId !== value)
      router.push(`/${projectId}/${value}/compare/${secondaryContractId}`);
  };
}

interface ComparisonSelectProps {
  secondary?: boolean;
  listFor?: CONTRACT_TYPES;
  comparisonContract?: ContractObject;
  selectedContractId: string;
  secondarySelectedContractId?: string;
  projectId: string;
  contractsList: ContractObject[];
}

export function ComparisonSelect(props: ComparisonSelectProps): JSX.Element {
  const [selectedContract, setSelectedContract] = useState<
    ContractObject | undefined
  >();
  const [contractOptions, setContractOptions] = useState<CommonSelectOption[]>(
    []
  );

  const handleSelection = useHandleSelection(
    props.secondary,
    props.projectId,
    props.selectedContractId,
    props.secondarySelectedContractId
  );

  useEffect(() => {
    setSelectedContract(props.comparisonContract);
    formatContractOptions(props.listFor);
  }, [props.listFor]);

  function formatContractOptions(type?: CONTRACT_TYPES): void {
    const options: CommonSelectOption[] = [];
    props.contractsList.filter((report) =>
      !type ? report : report.content_type !== type
    );
    if (props.contractsList.length === 0) {
      setContractOptions(options);
      return;
    }
    const vsow = props.contractsList.filter(
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
    const csow = props.contractsList.filter(
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
    const po = props.contractsList.filter(
      (contract) => contract.content_type === CONTRACT_TYPES.PURCHASE_ORDER
    );
    if (po.length > 0) {
      options.push({ value: "separatorPo", label: "PO", isSeparator: true });
      options.push(
        ...sortByLabelOrFileName(po).map((item) => {
          return {
            value: item.id.toString(),
            label: item.label ?? item.filename,
          };
        })
      );
    }
    const invoice = props.contractsList.filter(
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
