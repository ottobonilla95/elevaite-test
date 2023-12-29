import type { JSX } from "react";
import React from "react";
import type { WorkSheet } from "xlsx";
import XLSX from "xlsx";

interface OutTableProps {
  data: string[][];
  columns: { name: string; key: number }[];
  tableClassName?: string;
  tableHeaderRowClass?: string;
  className?: string;
  withZeroColumn?: boolean;
  withoutRowNum?: boolean;
  renderRowNum?: (row: unknown, index: number) => JSX.Element;
}

export function OutTable({
  data,
  columns,
  tableClassName,
  tableHeaderRowClass,
  className,
  withZeroColumn,
  withoutRowNum,
  renderRowNum,
}: OutTableProps): JSX.Element {
  return (
    <div className={className}>
      <table className={tableClassName}>
        <tbody>
          <tr>
            {withZeroColumn && !withoutRowNum ? <th className={tableHeaderRowClass || ""} /> : null}
            {columns.map((c) => (
              <th className={c.key === -1 ? tableHeaderRowClass : ""} key={c.key}>
                {c.key === -1 ? "" : c.name}
              </th>
            ))}
          </tr>
          {data.map((r, i) => (
            <tr key={i}>
              {!withoutRowNum && (
                <td className={tableHeaderRowClass} key={i}>
                  {renderRowNum ? renderRowNum(r, i) : i}
                </td>
              )}
              {columns.map((c) => (
                <td key={c.key}>{r[c.key]}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function ExcelWorkSheetRenderer(ws: WorkSheet): {
  rows: string[][];
  cols: { name: string; key: number }[];
} {
  if (!ws["!ref"]) throw new Error("Worksheet ref not found");

  /* Convert array of arrays */
  const json = XLSX.utils.sheet_to_json<string[]>(ws, { header: 1, blankrows: false });
  let lastWithData = 0;
  for (let index = 0; index < json.length; index++) {
    const element = json[index];
    if (element.length !== 0 && index > lastWithData) lastWithData = index;
  }

  const cols = makeCols(ws["!ref"]);

  return { rows: json, cols };
}

function makeCols(refstr: string): { name: string; key: number }[] {
  const o: { name: string; key: number }[] = [],
    C = XLSX.utils.decode_range(refstr).e.c + 1;
  for (let i = 0; i < C; ++i) {
    o[i] = { name: XLSX.utils.encode_col(i), key: i };
  }
  return o;
}
