import React, { useState } from 'react';

interface CustomerDataDebuggerProps {
    customerData: any;
    dateFilters: {
        startDate?: string;
        endDate?: string;
    };
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const CustomerDataDebugger: React.FC<CustomerDataDebuggerProps> = ({ customerData, dateFilters }) => {
    const [expanded, setExpanded] = useState(false);
    const [validationData, setValidationData] = useState<any>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const getUiDataSummary = () => {
        const summary: Record<string, any> = {
            uiDataSummary: {}
        };

        if (customerData) {
            if (customerData.concentrations) {
                summary.uiDataSummary.totalTickets = customerData.concentrations.totalTickets;
                summary.uiDataSummary.categoryCount = customerData.concentrations.data.length;

                summary.uiDataSummary.topCategories = customerData.concentrations.data
                    .slice(0, 3)
                    .map((cat: any) => ({
                        name: cat.name,
                        value: cat.value,
                        count: cat.count
                    }));
            }

            if (customerData.topCustomers) {
                summary.uiDataSummary.topCustomerCount = customerData.topCustomers.length;

                const totalRequests = customerData.topCustomers.reduce(
                    (sum: number, customer: any) => sum + customer.serviceRequests,
                    0
                );

                summary.uiDataSummary.topCustomerRequests = totalRequests;
            }
        }

        return summary;
    };

    const validateData = async () => {
        try {
            setLoading(true);
            setError(null);

            const params = new URLSearchParams();
            if (dateFilters.startDate) {
                params.append('start_date', dateFilters.startDate);
            }
            if (dateFilters.endDate) {
                params.append('end_date', dateFilters.endDate);
            }

            const queryString = params.toString() ? `?${params.toString()}` : '';

            const response = await fetch(`${API_URL}/api/analytics/customer/validate-data${queryString}`);

            if (!response.ok) {
                throw new Error(`Server responded with status: ${response.status}`);
            }

            const data = await response.json();

            if (data.status === 'error') {
                throw new Error(data.message || 'Unknown error occurred');
            }

            setValidationData(data.validation);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Unknown error');
            console.error('Error validating data:', err);
        } finally {
            setLoading(false);
        }
    };

    const getMismatchInfo = () => {
        if (!validationData || !customerData.concentrations) {
            return null;
        }

        const uiTotal = customerData.concentrations.totalTickets;
        const dbTotal = validationData.total_tickets;

        if (uiTotal !== dbTotal) {
            return {
                uiTotal,
                dbTotal,
                difference: Math.abs(uiTotal - dbTotal),
                percentDiff: Math.round(Math.abs(uiTotal - dbTotal) / dbTotal * 100 * 10) / 10
            };
        }

        return null;
    };

    const uiSummary = getUiDataSummary();
    const mismatch = getMismatchInfo();

    if (process.env.NODE_ENV === 'production') {
        return null;
    }

    return (
        <div style={{
            position: 'fixed',
            bottom: '20px',
            right: '20px',
            zIndex: 9999,
            padding: "12px",
            borderRadius: "6px",
            fontSize: "12px",
            fontWeight: "500",
            boxShadow: "0 2px 5px rgba(0,0,0,0.1)",
            backgroundColor: mismatch ? "#fed7aa" : "#d1fae5",
            color: mismatch ? "#9a3412" : "#065f46",
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
                <span style={{ fontWeight: 'bold' }}>Customer Data Debugger</span>
                {mismatch && (
                    <span style={{ marginLeft: '8px', color: '#ef4444' }}>
                        ⚠️ Count Mismatch!
                    </span>
                )}
            </div>

            <div style={{ fontSize: '11px', marginBottom: '8px' }}>
                UI Ticket Count: <strong>{customerData.concentrations?.totalTickets || 'N/A'}</strong>
                {validationData && (
                    <span style={{ marginLeft: '8px' }}>
                        DB Count: <strong>{validationData.total_tickets}</strong>
                    </span>
                )}
            </div>

            {mismatch && (
                <div style={{
                    padding: '6px',
                    backgroundColor: '#fef2f2',
                    borderRadius: '4px',
                    color: '#b91c1c',
                    marginBottom: '8px',
                    fontSize: '11px'
                }}>
                    <strong>Count Difference: {mismatch.difference} ({mismatch.percentDiff}%)</strong>
                    <div>UI shows {mismatch.uiTotal}, DB has {mismatch.dbTotal}</div>
                </div>
            )}

            {expanded && (
                <>
                    <button
                        onClick={(e) => {
                            e.stopPropagation();
                            validateData();
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
                        {loading ? "Loading..." : "Validate Customer Data"}
                    </button>

                    {error && (
                        <div style={{
                            padding: '6px',
                            backgroundColor: '#fef2f2',
                            borderRadius: '4px',
                            color: '#b91c1c',
                            marginBottom: '8px',
                            fontSize: '11px'
                        }}>
                            Error: {error}
                        </div>
                    )}

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
                        <div style={{ marginBottom: '4px', fontWeight: 'bold' }}>UI Data Summary:</div>
                        <pre style={{ margin: 0, fontSize: '10px' }}>
                            {JSON.stringify(uiSummary, null, 2)}
                        </pre>
                    </div>

                    {validationData && (
                        <>
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
                                <div style={{ fontWeight: 'bold', marginBottom: '4px' }}>Database Validation:</div>

                                <table style={{ width: '100%', fontSize: '10px', borderCollapse: 'collapse' }}>
                                    <tbody>
                                        <tr>
                                            <td style={{ padding: '3px', borderBottom: '1px solid #eee' }}>Total Tickets:</td>
                                            <td style={{ padding: '3px', borderBottom: '1px solid #eee', fontWeight: 'bold' }}>{validationData.total_tickets}</td>
                                        </tr>
                                        <tr>
                                            <td style={{ padding: '3px', borderBottom: '1px solid #eee' }}>With Problem Summary:</td>
                                            <td style={{ padding: '3px', borderBottom: '1px solid #eee' }}>{validationData.tickets_with_problems}</td>
                                        </tr>
                                        <tr>
                                            <td style={{ padding: '3px', borderBottom: '1px solid #eee' }}>Without Problem Summary:</td>
                                            <td style={{ padding: '3px', borderBottom: '1px solid #eee' }}>{validationData.tickets_no_problem_summary}</td>
                                        </tr>
                                        <tr>
                                            <td style={{ padding: '3px', borderBottom: '1px solid #eee' }}>Sum Check:</td>
                                            <td style={{ padding: '3px', borderBottom: '1px solid #eee', color: validationData.sum_check ? 'green' : 'red' }}>
                                                {validationData.sum_check ? '✓ Correct' : '✗ Mismatch'}
                                            </td>
                                        </tr>
                                        <tr>
                                            <td style={{ padding: '3px', borderBottom: '1px solid #eee' }}>Date Range:</td>
                                            <td style={{ padding: '3px', borderBottom: '1px solid #eee' }}>
                                                {validationData.date_range.min_date} to {validationData.date_range.max_date}
                                            </td>
                                        </tr>
                                    </tbody>
                                </table>

                                {validationData.category_distribution && (
                                    <>
                                        <div style={{ fontWeight: 'bold', marginTop: '8px', marginBottom: '4px' }}>Category Distribution:</div>
                                        <table style={{ width: '100%', fontSize: '10px', borderCollapse: 'collapse' }}>
                                            <thead>
                                                <tr>
                                                    <th style={{ textAlign: 'left', padding: '3px', borderBottom: '1px solid #ddd' }}>Category</th>
                                                    <th style={{ textAlign: 'right', padding: '3px', borderBottom: '1px solid #ddd' }}>Count</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {validationData.category_distribution.map((item: any, i: number) => (
                                                    <tr key={i}>
                                                        <td style={{ padding: '3px', borderBottom: '1px solid #eee' }}>{item.category}</td>
                                                        <td style={{ textAlign: 'right', padding: '3px', borderBottom: '1px solid #eee' }}>{item.count}</td>
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    </>
                                )}
                            </div>

                            {validationData.top_customers && (
                                <div style={{
                                    marginTop: '8px',
                                    padding: '8px',
                                    background: 'rgba(255, 255, 255, 0.8)',
                                    borderRadius: '4px',
                                    fontSize: '11px',
                                    color: '#333',
                                    overflow: 'auto',
                                    maxHeight: '150px'
                                }}>
                                    <div style={{ fontWeight: 'bold', marginBottom: '4px' }}>Top Customers:</div>
                                    <table style={{ width: '100%', fontSize: '10px', borderCollapse: 'collapse' }}>
                                        <thead>
                                            <tr>
                                                <th style={{ textAlign: 'left', padding: '3px', borderBottom: '1px solid #ddd' }}>Customer</th>
                                                <th style={{ textAlign: 'right', padding: '3px', borderBottom: '1px solid #ddd' }}>Tickets</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {validationData.top_customers.map((item: any, i: number) => (
                                                <tr key={i}>
                                                    <td style={{ padding: '3px', borderBottom: '1px solid #eee' }}>{item.customer}</td>
                                                    <td style={{ textAlign: 'right', padding: '3px', borderBottom: '1px solid #eee' }}>{item.tickets}</td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            )}
                        </>
                    )}
                </>
            )}

            <div style={{
                fontSize: '10px',
                marginTop: '8px',
                opacity: 0.8,
                textAlign: 'center'
            }}>
                Click to {expanded ? 'collapse' : 'examine'} data {expanded ? '▲' : '▼'}
            </div>
        </div>
    );
};

export default CustomerDataDebugger;