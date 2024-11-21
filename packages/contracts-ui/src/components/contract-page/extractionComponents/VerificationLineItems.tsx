import {
  CommonButton,
  CommonModal,
  ElevaiteIcons,
  SimpleInput,
} from "@repo/ui/components";
import { useEffect, useState } from "react";
import {
  type ContractObject,
  type ContractProjectObject,
  type ContractObjectVerificationLineItem,
  type ContractObjectVerificationLineItemVerification,
  type LoadingListObject,
} from "../../../interfaces";
import "./VerificationLineItems.scss";

interface TableDataItem {
  value: (string | number | null | undefined)[];
  verification: ContractObjectVerificationLineItemVerification;
}

interface VerificationLineItemsProps {
  selectedProject?: ContractProjectObject;
  selectedContract?: ContractObject;
  lineItems?: ContractObjectVerificationLineItem[];
  loading: LoadingListObject;
  fullScreen?: boolean;
  onFullScreenClose?: () => void;
}

export function VerificationLineItems(
  props: VerificationLineItemsProps
): JSX.Element {
  const [displayHeaders, setDisplayHeaders] =
    useState<string[]>(getFullHeaderData());
  const [tableData, setTableData] = useState<TableDataItem[]>();

  useEffect(() => {
    if (props.lineItems) {
      const data = getTableData(props.lineItems, getFullHeaderData());
      setTableData(data.table);
      setDisplayHeaders(data.headers);
    }
  }, [props.lineItems]);

  function handleClose(): void {
    if (props.onFullScreenClose) props.onFullScreenClose();
  }

  function getFullHeaderData(): string[] {
    const originalHeaders = [
      "Ver.",
      "Amount",
      "Quantity",
      "Unit Price",
      "Product Code",
      "Need by",
      "Description",
    ];
    if (!props.lineItems || !props.selectedProject?.settings?.labels)
      return originalHeaders;
    const formattedHeaders = ["Ver."];
    const labels = props.selectedProject?.settings?.labels;

    // Consider making this automated by iterating keys (ordering, though?)
    formattedHeaders.push(labels.total_cost ?? "Total Cost");
    formattedHeaders.push(labels.quantity ?? "Quantity");
    formattedHeaders.push(labels.unit_cost ?? "Unit Cost");
    formattedHeaders.push(labels.product_identifier ?? "Product Identifier");
    formattedHeaders.push(labels.need_by_date ?? "Need By");
    formattedHeaders.push(labels.ibx ?? "IBX");
    formattedHeaders.push(labels.site_name ?? "Site Name");
    formattedHeaders.push(labels.site_address ?? "Site Address");
    formattedHeaders.push(labels.description ?? "Description");

    return formattedHeaders;
  }

  function getTableData(
    lineItems: ContractObjectVerificationLineItem[],
    headers: string[]
  ): { table: TableDataItem[]; headers: string[] } {
    const isColumnEmpty = Array(headers.length).fill(true);

    lineItems.forEach((item) => {
      const values = [
        true,
        item.amount,
        item.quantity,
        item.unit_price,
        item.product_identifier,
        item.need_by_date,
        item.ibx,
        item.site_name,
        item.site_address,
        item.description,
      ];
      values.forEach((value, i) => {
        if (value !== null && value !== undefined && value !== "") {
          isColumnEmpty[i] = false;
        }
      });
    });

    const filteredHeaders = headers.filter((_, index) => !isColumnEmpty[index]);

    const data = lineItems.map((item, index) => {
      const values = [
        index + 1,
        item.amount,
        item.quantity,
        item.unit_price,
        item.product_identifier,
        item.need_by_date,
        item.ibx,
        item.site_name,
        item.site_address,
        item.description,
      ];
      const filteredValues = values.filter((_, i) => !isColumnEmpty[i]);

      return {
        value: filteredValues,
        verification: item.verification,
      };
    });

    return { table: data, headers: filteredHeaders };
  }

  return (
    <div className="verification-line-items-container">
      <div className="table-scroller">
        {props.loading.contractLineItems[props.selectedContract?.id ?? ""] ? (
          <div className="loading">
            <ElevaiteIcons.SVGSpinner />
          </div>
        ) : !tableData ? (
          <div>No tabular data available</div>
        ) : (
          <VerificationTableStructure
            headers={displayHeaders}
            data={tableData}
          />
        )}
      </div>

      {!props.fullScreen || !tableData ? undefined : (
        <CommonModal
          className="full-screen-extracted-line-items-modal"
          onClose={handleClose}
        >
          <div className="close-button-area">
            <CommonButton onClick={handleClose} noBackground>
              <ElevaiteIcons.SVGXmark />
            </CommonButton>
          </div>
          <div className="table-scroller">
            <VerificationTableStructure
              headers={displayHeaders}
              data={tableData}
            />
          </div>
        </CommonModal>
      )}
    </div>
  );
}

interface VerificationTableStructureProps {
  headers: string[];
  data: TableDataItem[];
}

function VerificationTableStructure(
  props: VerificationTableStructureProps
): JSX.Element {
  return (
    <table className="line-items-table">
      <thead>
        <tr>
          {props.headers.map((header, headerIndex) => (
            <th key={header} className={props.headers[headerIndex]}>
              {header}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {props.data.map((row, rowIndex) => (
          <tr key={`line_${rowIndex.toString()}`}>
            {row.value.map((cell, cellIndex) => (
              <td
                key={`column_${cellIndex.toString()}`}
                className={props.headers[cellIndex]}
              >
                {cellIndex === 0 ? (
                  <div
                    className={[
                      "verification",
                      row.verification.verification_status
                        ? "verified"
                        : undefined,
                    ]
                      .filter(Boolean)
                      .join(" ")}
                    title={`VSOW: ${row.verification.vsow ? "Verified" : "Failed"}\nPO: ${row.verification.po ? "Verified" : "Failed"}\nInvoice: ${row.verification.invoice ? "Verified" : "Failed"}\n`}
                  >
                    {/* <div>{cell !== null ? cell.toString() : ""}</div> */}
                    {row.verification.verification_status ? (
                      <ElevaiteIcons.SVGCheckmark />
                    ) : (
                      <ElevaiteIcons.SVGXmark />
                    )}
                  </div>
                ) : (
                  <SimpleInput
                    value={
                      cell !== null && cell !== undefined ? cell.toString() : ""
                    }
                    title={
                      cell !== null &&
                        cell !== undefined &&
                        cell.toString().length > 30
                        ? cell.toString()
                        : ""
                    }
                    autoSize
                    disabled
                  />
                )}
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}
