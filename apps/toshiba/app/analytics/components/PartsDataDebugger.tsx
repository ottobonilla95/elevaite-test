import React, { useState, useEffect } from 'react';

// Define proper interfaces to match your data structure
interface CustomerPart {
    customer: string;
    customerAccount: string;
    partNumber: string;
    partDescription: string;
    partType: string;
    replacementCount: number;
    totalCost: number;
}

interface MachinePart {
    machineType: string;
    partNumber: string;
    partDescription: string;
    count: number;
    cost: number;
}

interface PartsSummary {
    uniquePartsCount: number;
    totalCost: number;
    totalReplacements: number;
    serviceRequestsWithParts: number;
}

interface Customer {
    name: string;
    account: string;
    count: number;
}

interface PartsData {
    customers?: Customer[];
    partsData?: CustomerPart[];
    machinePartsData?: MachinePart[];
    summary?: PartsSummary | null;
    error?: string | null;
}

interface PartsDataDebuggerProps {
    partsData: PartsData;
    dateFilters: {
        startDate?: string;
        endDate?: string;
    };
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const PartsDataDebugger: React.FC<PartsDataDebuggerProps> = ({ partsData, dateFilters }) => {
    const [expanded, setExpanded] = useState(false);
    const [databaseInfo, setDatabaseInfo] = useState<any>(null);
    const [loading, setLoading] = useState(false);

    // Check if we have some parts data
    const hasPartsData = partsData &&
        partsData.partsData &&
        partsData.partsData.length > 0;

    // Get a summary of the parts data
    const getPartsSummary = () => {
        if (!partsData) return { summary: "No parts data available" };

        const summary: Record<string, any> = {};

        if (partsData.summary) {
            summary.totalParts = partsData.summary.uniquePartsCount || 0;
            summary.totalCost = partsData.summary.totalCost || 0;
            summary.totalReplacements = partsData.summary.totalReplacements || 0;
            summary.serviceRequestsWithParts = partsData.summary.serviceRequestsWithParts || 0;
        }

        if (partsData.partsData) {
            summary.availableParts = partsData.partsData.length;

            // Get top 3 parts by replacement count
            const topParts = partsData.partsData
                .slice(0, 3)
                .map((part: CustomerPart) => ({
                    partNumber: part.partNumber,
                    description: part.partDescription,
                    count: part.replacementCount,
                    cost: part.totalCost
                }));

            summary.topParts = topParts;
        }

        if (partsData.machinePartsData) {
            summary.machineTypeCount = new Set(
                partsData.machinePartsData.map((item: MachinePart) => item.machineType)
            ).size;
        }

        return summary;
    };

    // Fetch database table info to check parts_used table
    const checkPartsTable = async () => {
        try {
            setLoading(true);

            const response = await fetch(`${API_URL}/api/debug/database-inspection`);

            if (!response.ok) {
                throw new Error(`Server responded with status: ${response.status}`);
            }

            const data = await response.json();

            // Extract parts_used info from the response
            const partsInfo = {
                tableExists: data.inspection.table_counts?.parts_used > 0,
                rowCount: data.inspection.table_counts?.parts_used || 0,
                sampleData: data.inspection.sample_data?.parts_used || []
            };

            setDatabaseInfo(partsInfo);
        } catch (error) {
            console.error("Error checking parts table:", error);
        } finally {
            setLoading(false);
        }
    };

    const summary = getPartsSummary();

    // Return nothing in production mode
    if (process.env.NODE_ENV === 'production') {
        return null;
    }

    return (
        <div style={{
            position: 'fixed',
            bottom: '20px',
            left: '20px',
            zIndex: 9999,
            padding: "12px",
            borderRadius: "6px",
            fontSize: "12px",
            fontWeight: "500",
            boxShadow: "0 2px 5px rgba(0,0,0,0.1)",
            backgroundColor: hasPartsData ? "#d1fae5" : "#fef3c7",
            color: hasPartsData ? "#065f46" : "#92400e",
            maxWidth: expanded ? "600px" : "300px",
            maxHeight: expanded ? "80vh" : "auto",
            overflow: "auto",
        }}
            onClick={() => setExpanded(!expanded)}
        >
            <div style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                marginBottom: '4px'
            }}>
                <span style={{ fontWeight: 'bold' }}>Parts Data Debugger</span>
                <span style={{ marginLeft: '8px' }}>
                    {hasPartsData ? "✅ Parts Data Found" : "⚠️ No Parts Data"}
                </span>
            </div>

            <div style={{ fontSize: '11px', marginBottom: '8px' }}>
                Unique Parts: <strong>{summary.totalParts || 0}</strong>
                <span style={{ marginLeft: '8px' }}>
                    Total Cost: <strong>${summary.totalCost?.toLocaleString() || 0}</strong>
                </span>
            </div>

            {partsData.error && (
                <div style={{
                    padding: '6px',
                    fontSize: '11px',
                    backgroundColor: '#fef2f2',
                    borderRadius: '4px',
                    color: '#b91c1c',
                    marginBottom: '8px'
                }}>
                    Error: {partsData.error}
                </div>
            )}

            {expanded && (
                <>
                    <button
                        onClick={(e) => {
                            e.stopPropagation();
                            checkPartsTable();
                        }}
                        style={{
                            backgroundColor: "#4b5563",
                            color: "white",
                            border: "none",
                            padding: "6px 12px",
                            borderRadius: "4px",
                            fontSize: "11px",
                            cursor: "pointer",
                            marginTop: "4px",
                            marginBottom: "8px",
                            width: "100%"
                        }}
                    >
                        {loading ? "Loading..." : "Check Database Parts Table"}
                    </button>

                    <div style={{
                        marginTop: '8px',
                        padding: '8px',
                        background: 'rgba(255, 255, 255, 0.8)',
                        borderRadius: '4px',
                        fontSize: '11px',
                        color: '#333',
                        fontFamily: 'monospace',
                        overflow: 'auto',
                        maxHeight: '100px'
                    }}>
                        <div style={{ marginBottom: '4px', fontWeight: 'bold' }}>Parts Data Summary:</div>
                        <pre style={{ margin: 0, fontSize: '10px' }}>
                            {JSON.stringify(summary, null, 2)}
                        </pre>
                    </div>

                    {databaseInfo && (
                        <div style={{
                            marginTop: '8px',
                            padding: '8px',
                            background: 'rgba(255, 255, 255, 0.8)',
                            borderRadius: '4px',
                            fontSize: '11px',
                            color: '#333',
                            overflow: 'auto',
                            maxHeight: '200px'
                        }}>
                            <div style={{ fontWeight: 'bold', marginBottom: '4px' }}>Parts Table in Database:</div>

                            <table style={{ width: '100%', fontSize: '10px', borderCollapse: 'collapse' }}>
                                <tbody>
                                    <tr>
                                        <td style={{ padding: '3px', borderBottom: '1px solid #eee' }}>Table exists:</td>
                                        <td style={{ padding: '3px', borderBottom: '1px solid #eee', fontWeight: 'bold', color: databaseInfo.tableExists ? 'green' : 'red' }}>
                                            {databaseInfo.tableExists ? '✓ Yes' : '✗ No'}
                                        </td>
                                    </tr>
                                    <tr>
                                        <td style={{ padding: '3px', borderBottom: '1px solid #eee' }}>Row count:</td>
                                        <td style={{ padding: '3px', borderBottom: '1px solid #eee' }}>
                                            {databaseInfo.rowCount}
                                        </td>
                                    </tr>
                                </tbody>
                            </table>

                            {databaseInfo.sampleData.length > 0 && (
                                <>
                                    <div style={{ fontWeight: 'bold', marginTop: '8px', marginBottom: '4px' }}>Sample Parts Data:</div>
                                    <table style={{ width: '100%', fontSize: '10px', borderCollapse: 'collapse' }}>
                                        <thead>
                                            <tr>
                                                {Object.keys(databaseInfo.sampleData[0]).map((key) => (
                                                    <th key={key} style={{ textAlign: 'left', padding: '3px', borderBottom: '1px solid #ddd' }}>
                                                        {key}
                                                    </th>
                                                ))}
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {databaseInfo.sampleData.map((item: any, index: number) => (
                                                <tr key={index}>
                                                    {Object.entries(item).map(([key, value]) => (
                                                        <td key={key} style={{ padding: '3px', borderBottom: '1px solid #eee' }}>
                                                            {String(value).substring(0, 15)}{String(value).length > 15 ? '...' : ''}
                                                        </td>
                                                    ))}
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </>
                            )}
                        </div>
                    )}
                </>
            )}

            <div style={{
                fontSize: '10px',
                marginTop: '8px',
                opacity: 0.8,
                textAlign: 'center'
            }}>
                Click to {expanded ? 'collapse' : 'examine'} parts data {expanded ? '▲' : '▼'}
            </div>
        </div>
    );
};

export default PartsDataDebugger;