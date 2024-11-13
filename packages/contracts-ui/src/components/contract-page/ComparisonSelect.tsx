import { useEffect, useState } from "react";
import { CommonSelect, type CommonSelectOption } from "@repo/ui/components";
import { usePathname, useRouter } from "next/navigation";
import { CONTRACT_TYPES, type ContractObject } from "@/interfaces";
import "./ComparisonSelect.scss";
import { getContractProjectContracts } from "@/actions/contractActions";

interface ComparisonSelectProps {
  secondary?: boolean;
  listFor?: CONTRACT_TYPES;
  selectedContract?: ContractObject;
  secondarySelectedContract?: ContractObject;
  projectId: string;
}

function useHandleSelection(
  secondary: boolean | undefined,
  newContractId: string
) {
  const router = useRouter();
  const currentPath = usePathname();

  return () => {
    const pathParts = currentPath.split("/");
    if (!secondary) {
      pathParts[2] = newContractId;
    } else {
      pathParts[4] = newContractId;
    }
    const newPath = pathParts.join("/");
    router.replace(newPath);
  };
}

export function ComparisonSelect(props: ComparisonSelectProps): JSX.Element {
  const [selectedContract, setSelectedContract] = useState<
    ContractObject | undefined
  >();
  const [contractOptions, setContractOptions] = useState<CommonSelectOption[]>(
    []
  );

  const handleSelection = useHandleSelection(props.secondary, props.projectId);

  useEffect(() => {
    if (!props.secondary) setSelectedContract(props.selectedContract);
    else if (
      props.secondarySelectedContract &&
      typeof props.secondarySelectedContract === "object"
    )
      setSelectedContract(props.secondarySelectedContract);
    formatContractOptions(props.listFor);
  }, [props.listFor]);

  function formatContractOptions(type?: CONTRACT_TYPES): void {
    const options: CommonSelectOption[] = [];
    getContractProjectContracts(props.projectId, false).then((contracts) => {
      contracts.filter((report) =>
        !type ? report : report.content_type !== type
      );
      if (!contracts || contracts.length === 0) {
        setContractOptions(options);
        return;
      }
      const vsow = contracts.filter(
        (contract) => contract.content_type === CONTRACT_TYPES.VSOW
      );
      if (vsow && vsow.length > 0) {
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
      if (csow && csow.length > 0) {
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
      if (po && po.length > 0) {
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
      const invoice = contracts.filter(
        (contract) => contract.content_type === CONTRACT_TYPES.INVOICE
      );
      if (invoice && invoice.length > 0) {
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
    });

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
