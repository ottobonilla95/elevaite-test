import React, { useState } from "react";
import "./Table.scss";

export interface Column<T> {
    label: string;
    key: keyof T;
    render?: (value: any, row: T) => React.ReactNode;
}

interface TableProps<T> {
    data: T[];
    columns: Column<T>[];
    title: string;
    showExportButton?: boolean;
    showPagination?: boolean;
}

const Table = <T,>({ data, columns, title, showExportButton, showPagination }: TableProps<T>) => {
    const [currentPage, setCurrentPage] = useState(1);
    const [itemsPerPage, setItemsPerPage] = useState(5);
    const totalPages = Math.ceil(data.length / itemsPerPage);

    const handlePageChange = (page: number) => {
        setCurrentPage(page);
    };

    const getPageNumbers = () => {
        const pages: (number | string)[] = [];
        if (totalPages <= 5) {
            for (let i = 1; i <= totalPages; i++) pages.push(i);
        } else {
            if (currentPage <= 3) {
                pages.push(1, 2, 3, 4, "...", totalPages);
            } else if (currentPage >= totalPages - 2) {
                pages.push(1, "...", totalPages - 3, totalPages - 2, totalPages - 1, totalPages);
            } else {
                pages.push(1, "...", currentPage - 1, currentPage, currentPage + 1, "...", totalPages);
            }
        }
        return pages;
    };

    return (
        <div className="replacement-parts-container">

            <table>
                <thead>
                    <tr>
                        {columns.map((column, index) => (
                            <th key={index}>{column.label}</th>
                        ))}
                    </tr>
                </thead>
                <tbody>
                    {(showPagination ?
                        data.slice((currentPage - 1) * itemsPerPage, currentPage * itemsPerPage) :
                        data
                    ).map((row, rowIndex) => (
                        <tr key={rowIndex}>
                            {columns.map((column, colIndex) => {
                                const value = row[column.key];
                                return (
                                    <td key={colIndex}>
                                        {column.render ? column.render(value, row) : (value as React.ReactNode)}
                                    </td>
                                );
                            })}
                        </tr>
                    ))}
                </tbody>
            </table>

            {showPagination && (
                <div className="pagination-container">
                    <div className="entries-info">
                        Showing {(currentPage - 1) * itemsPerPage + 1} to{" "}
                        {Math.min(currentPage * itemsPerPage, data.length)} of {data.length} entries
                    </div>

                    <div className="pagination-pages">
                        {getPageNumbers().map((page, index) => (
                            <button
                                key={index}
                                onClick={() => typeof page === "number" && handlePageChange(page)}
                                className={`pagination-page ${page === currentPage ? "active" : ""}`}
                                disabled={page === "..."}
                            >
                                {page}
                            </button>
                        ))}
                        <select
                            value={itemsPerPage}
                            onChange={(e) => {
                                setItemsPerPage(Number(e.target.value));
                                setCurrentPage(1);
                            }}
                            className="items-per-page"
                        >
                            {[5, 10, 25, 50].map((num) => (
                                <option key={num} value={num}>
                                    {num} / page
                                </option>
                            ))}
                        </select>
                    </div>

                    <div className="pagination-buttons">
                        <button
                            onClick={() => handlePageChange(currentPage - 1)}
                            disabled={currentPage === 1}
                            className="pagination-button"
                        >
                            &lt; Back
                        </button>
                        <button
                            onClick={() => handlePageChange(currentPage + 1)}
                            disabled={currentPage === totalPages}
                            className="pagination-button"
                        >
                            Next &gt;
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
};

export default Table;

