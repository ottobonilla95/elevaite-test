import React, { useState, useEffect } from 'react';

interface ServiceDataDebuggerProps {
    serviceData: any;
    dateFilters: {
        startDate?: string;
        endDate?: string;
    };
    selectedCustomer?: string;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const ServiceDataDebugger: React.FC<ServiceDataDebuggerProps> = ({ serviceData, dateFilters, selectedCustomer }) => {
    const [expanded, setExpanded] = useState(false);
    const [validationData, setValidationData] = useState<any>(null);
    const [loading, setLoading] = useState(false);

    // Get a summary of the service data
    const getServiceSummary = () => {
        if (!serviceData) return { summary: "No service data available" };

        const summary: Record<string, any> = {};

        // Extract information from the metrics
        if (serviceData.metrics) {
            summary.travelTime = serviceData.metrics.travel_time?.average || 0;
            summary.serviceTime = serviceData.metrics.service_time?.average || 0;
            summary.topTechnician = serviceData.metrics.top_technician?.name || 'N/A';
            summary.technicianCount = serviceData.metrics.top_technician?.count || 0;
        }

        // Extract time analysis
        if (serviceData.timeAnalysis) {
            summary.totalTime = serviceData.timeAnalysis.overview?.totalTime || 0;
            summary.efficiency = serviceData.timeAnalysis.overview ?
                ((serviceData.timeAnalysis.overview.serviceTime / serviceData.timeAnalysis.overview.totalTime) * 100).toFixed(1) + '%' :
                'N/A';

            // Get machine types
            if (serviceData.timeAnalysis.byMachineType) {
                summary.machineTypeCount = serviceData.timeAnalysis.byMachineType.length;

                // Get top 3 machine types
                summary.topMachineTypes = serviceData.timeAnalysis.byMachineType
                    .slice(0, 3)
                    .map((machine: any) => ({
                        type: machine.machineType,
                        serviceTime: machine.serviceTime,
                        travelTime: machine.travelTime
                    }));
            }
        }

        // Extract trend data
        if (serviceData.trendData) {
            summary.trendPoints = serviceData.trendData.length;
            summary.firstTrendDate = serviceData.trendData[0]?.date || 'N/A';
            summary.lastTrendDate = serviceData.trendData[serviceData.trendData.length - 1]?.date || 'N/A';
        }

        // Extract severity data
        if (serviceData.severityData) {
            summary.severityCount = serviceData.severityData.length;
            summary.severityDistribution = serviceData.severityData.map((item: any) => ({
                label: item.label,
                count: item.count
            }));
        }

        return summary;
    };

    // Validate data from backend
    const validateData = async () => {
        try {
            setLoading(true);

            // Build query parameters
            const params = new URLSearchParams();
            if (dateFilters.startDate) {
                params.append('start_date', dateFilters.startDate);
            }
            if (dateFilters.endDate) {
                params.append('end_date', dateFilters.endDate);
            }
            if (selectedCustomer) {
                params.append('customer', selectedCustomer);
            }

            const queryString = params.toString() ? `?${params.toString()}` : '';

            // Call the validation endpoint
            const response = await fetch(`${API_URL}/api/analytics/service/validate-data${queryString}`);

            if (!response.ok) {
                throw new Error(`Server responded with status: ${response.status}`);
            }

            const data = await response.json();

            if (data.status === 'error') {
                throw new Error(data.message || 'Unknown error occurred');
            }

            setValidationData(data.validation);
        } catch (err) {
            console.error('Error validating data:', err);
        } finally {
            setLoading(false);
        }
    };

    const summary = getServiceSummary();

    // Check if we have metrics and time analysis
    const hasServiceData = serviceData && serviceData.metrics && serviceData.timeAnalysis;

    // Return nothing in production mode
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
            backgroundColor: hasServiceData ? "#d1fae5" : "#fef3c7",
            color: hasServiceData ? "#065f46" : "#92400e",
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
                <span style={{ fontWeight: 'bold' }}>Service Data Debugger</span>
                <span style={{ marginLeft: '8px' }}>
                    {hasServiceData ? "✅ Service Data Found" : "⚠️ No Service Data"}
                </span>
            </div>

            <div style={{ fontSize: '11px', marginBottom: '8px' }}>
                Travel Time: <strong>{serviceData?.metrics?.travel_time?.formatted || 'N/A'}</strong>
                <span style={{ marginLeft: '8px' }}>
                    Service Time: <strong>{serviceData?.metrics?.service_time?.formatted || 'N/A'}</strong>
                </span>
            </div>

            {expanded && (
                <>
                    <div style={{ fontSize: '11px', marginBottom: '8px' }}>
                        Customer: <strong>{selectedCustomer || 'All Customers'}</strong>
                    </div>

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
                        {loading ? "Loading..." : "Validate Service Data"}
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
                        <div style={{ marginBottom: '4px', fontWeight: 'bold' }}>Service Data Summary:</div>
                        <pre style={{ margin: 0, fontSize: '10px' }}>
                            {JSON.stringify(summary, null, 2)}
                        </pre>
                    </div>

                    {validationData && (
                        <div style={{
                            marginTop: '8px',
                            padding: '8px',
                            background: 'rgba(255, 255, 255, 0.8)',
                            borderRadius: '4px',
                            fontSize: '11px',
                            color: '#333',
                            overflow: 'auto',
                            maxHeight: '300px'
                        }}>
                            <div style={{ fontWeight: 'bold', marginBottom: '4px' }}>Database Validation:</div>

                            <table style={{ width: '100%', fontSize: '10px', borderCollapse: 'collapse' }}>
                                <tbody>
                                    <tr>
                                        <td style={{ padding: '3px', borderBottom: '1px solid #eee' }}>Total Requests:</td>
                                        <td style={{ padding: '3px', borderBottom: '1px solid #eee', fontWeight: 'bold' }}>
                                            {validationData.total_requests}
                                        </td>
                                    </tr>
                                    <tr>
                                        <td style={{ padding: '3px', borderBottom: '1px solid #eee' }}>Total Tasks:</td>
                                        <td style={{ padding: '3px', borderBottom: '1px solid #eee' }}>
                                            {validationData.total_tasks}
                                        </td>
                                    </tr>
                                    <tr>
                                        <td style={{ padding: '3px', borderBottom: '1px solid #eee' }}>Avg Travel Time:</td>
                                        <td style={{ padding: '3px', borderBottom: '1px solid #eee' }}>
                                            {validationData.travel_time?.average} hours (from {validationData.travel_time?.count} records)
                                        </td>
                                    </tr>
                                    <tr>
                                        <td style={{ padding: '3px', borderBottom: '1px solid #eee' }}>Avg Service Time:</td>
                                        <td style={{ padding: '3px', borderBottom: '1px solid #eee' }}>
                                            {validationData.service_time?.average} hours (from {validationData.service_time?.count} records)
                                        </td>
                                    </tr>
                                    <tr>
                                        <td style={{ padding: '3px', borderBottom: '1px solid #eee' }}>Date Range:</td>
                                        <td style={{ padding: '3px', borderBottom: '1px solid #eee' }}>
                                            {validationData.date_range?.min_date} to {validationData.date_range?.max_date}
                                        </td>
                                    </tr>
                                </tbody>
                            </table>

                            {validationData.top_technicians && (
                                <>
                                    <div style={{ fontWeight: 'bold', marginTop: '8px', marginBottom: '4px' }}>Top Technicians:</div>
                                    <table style={{ width: '100%', fontSize: '10px', borderCollapse: 'collapse' }}>
                                        <thead>
                                            <tr>
                                                <th style={{ textAlign: 'left', padding: '3px', borderBottom: '1px solid #ddd' }}>Technician</th>
                                                <th style={{ textAlign: 'right', padding: '3px', borderBottom: '1px solid #ddd' }}>Count</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {validationData.top_technicians.map((tech: any, i: number) => (
                                                <tr key={i}>
                                                    <td style={{ padding: '3px', borderBottom: '1px solid #eee' }}>{tech.name}</td>
                                                    <td style={{ textAlign: 'right', padding: '3px', borderBottom: '1px solid #eee' }}>{tech.count}</td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </>
                            )}

                            {validationData.machine_types && (
                                <>
                                    <div style={{ fontWeight: 'bold', marginTop: '8px', marginBottom: '4px' }}>Machine Types:</div>
                                    <table style={{ width: '100%', fontSize: '10px', borderCollapse: 'collapse' }}>
                                        <thead>
                                            <tr>
                                                <th style={{ textAlign: 'left', padding: '3px', borderBottom: '1px solid #ddd' }}>Type</th>
                                                <th style={{ textAlign: 'right', padding: '3px', borderBottom: '1px solid #ddd' }}>Count</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {validationData.machine_types.map((type: any, i: number) => (
                                                <tr key={i}>
                                                    <td style={{ padding: '3px', borderBottom: '1px solid #eee' }}>{type.type}</td>
                                                    <td style={{ textAlign: 'right', padding: '3px', borderBottom: '1px solid #eee' }}>{type.count}</td>
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
                Click to {expanded ? 'collapse' : 'examine'} service data {expanded ? '▲' : '▼'}
            </div>
        </div>
    );
};

export default ServiceDataDebugger;