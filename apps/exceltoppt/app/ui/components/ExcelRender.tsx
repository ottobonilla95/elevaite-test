import type { JSX } from "react";
import React from "react";
import type { WorkSheet } from "xlsx";
import XLSX from "xlsx";

interface OutTableProps {
  data: StringOrUndefined[][];
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
            {withZeroColumn && !withoutRowNum ? (
              <th className={tableHeaderRowClass ?? ""} />
            ) : null}
            {columns.map((c) => (
              <th
                className={c.key === -1 ? tableHeaderRowClass : ""}
                key={c.key}
              >
                {c.key === -1 ? "" : c.name}
              </th>
            ))}
          </tr>
          {data.map((r, i) => (
            <tr key={`row${(i + 1).toString()}`}>
              {!withoutRowNum && (
                <td
                  className={tableHeaderRowClass}
                  key={`rowHeader${(i + 1).toString()}`}
                >
                  {renderRowNum ? renderRowNum(r, i) : i}
                </td>
              )}
              {columns.map((c) => (
                <td
                  className="border border-solid border-[#E5E5E5] text-[#171717b8] font-medium text-sm"
                  key={c.key}
                >
                  {r[c.key]}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export type StringOrUndefined = string | undefined;

export function ExcelWorkSheetRenderer(ws: WorkSheet): {
  rows: StringOrUndefined[][];
  cols: { name: string; key: number }[];
} {
  if (!ws["!ref"]) throw new Error("Worksheet ref not found");

  /* Convert array of arrays */
  const json = XLSX.utils.sheet_to_json<StringOrUndefined[]>(ws, {
    header: 1,
    blankrows: false,
  });
  let lastWithData = 0;
  let lastColWithData = 0;
  for (let index = 0; index < json.length; index++) {
    const element = json[index];
    // const last = element.reduce((prev, curr) => (curr ? curr : prev));
    let _indexOfLastDatum = 0;

    for (let _index = 0; _index < element.length; _index++) {
      const _element = element[_index];
      if (_element !== undefined) _indexOfLastDatum = _index;
    }

    if (lastColWithData < _indexOfLastDatum)
      lastColWithData = _indexOfLastDatum - 1;
    if (element.length !== 0 && index > lastWithData) lastWithData = index;
  }

  // const cols = makeCols(`A1`);
  const cols: { name: string; key: number }[] = [];
  for (let i = 0; i < lastColWithData; ++i) {
    cols[i] = { name: XLSX.utils.encode_col(i), key: i };
  }
  return { rows: json, cols };
}

// eslint-disable-next-line @typescript-eslint/no-unused-vars -- Might revert to this
function makeCols(refstr: string): { name: string; key: number }[] {
  const o: { name: string; key: number }[] = [],
    C = XLSX.utils.decode_range(refstr).e.c + 1;
  for (let i = 0; i < C; ++i) {
    o[i] = { name: XLSX.utils.encode_col(i), key: i };
  }
  return o;
}
