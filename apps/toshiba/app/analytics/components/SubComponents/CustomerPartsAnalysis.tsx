"use client";

import React, { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Cell, ResponsiveContainer } from 'recharts';
import { FiBox, FiDollarSign, FiRefreshCw, FiAlertCircle } from 'react-icons/fi';
import { fetchCustomerParts } from '../../lib/actions';
import StatCard from './StatCard';
import PartsDataDebugger from '../PartsDataDebugger';

interface CustomerPartsAnalysisProps {
    dateFilters: {
        startDate?: string;
        endDate?: string;
    };
}

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

interface PartsDataResponse {
    customers?: Customer[];
    partsData?: CustomerPart[];
    machinePartsData?: MachinePart[];
    summary?: PartsSummary;
}

const CustomerPartsAnalysis: React.FC<CustomerPartsAnalysisProps> = ({ dateFilters }) => {
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [customerOptions, setCustomerOptions] = useState<Customer[]>([]);
    const [selectedCustomer, setSelectedCustomer] = useState<string>("");
    const [partsData, setPartsData] = useState<CustomerPart[]>([]);
    const [machinePartsData, setMachinePartsData] = useState<MachinePart[]>([]);
    const [summary, setSummary] = useState<PartsSummary | null>(null);

    useEffect(() => {
        loadPartsData();
    }, [dateFilters, selectedCustomer]);

    const loadPartsData = async () => {
        try {
            setLoading(true);
            setError(null);

            const filters = {
                start_date: dateFilters.startDate,
                end_date: dateFilters.endDate,
                customer_account: selectedCustomer || undefined
            };

            const data = await fetchCustomerParts(filters);

            const response = data as PartsDataResponse;
            setCustomerOptions(response.customers || []);
            setPartsData(response.partsData || []);
            setMachinePartsData(response.machinePartsData || []);
            setSummary(response.summary || {
                uniquePartsCount: 0,
                totalCost: 0,
                totalReplacements: 0,
                serviceRequestsWithParts: 0
            });
        } catch (error) {
            console.error("Error loading parts data:", error);
            setError("Unable to load parts data. There may not be any parts records in the database.");
            // Set empty data on error
            setPartsData([]);
            setMachinePartsData([]);
            setSummary({
                uniquePartsCount: 0,
                totalCost: 0,
                totalReplacements: 0,
                serviceRequestsWithParts: 0
            });
        } finally {
            setLoading(false);
        }
    };

    const topPartsData = partsData
        .slice(0, 10)
        .map(part => ({
            name: part.partNumber || "Unknown Part#",
            partNumber: part.partNumber,
            partDescription: part.partDescription,
            count: part.replacementCount,
            customer: part.customer,
            cost: part.totalCost,

            color: `rgba(255, 107, 0, ${0.3 + Math.min(0.7, part.totalCost / 5000)})`
        }));

    const hasData = partsData.length > 0;

    if (loading) {
        return (
            <div className="customer-parts-analysis">
                <h2>Parts Replacement Analysis</h2>
                <div style={{ display: 'flex', justifyContent: 'center', padding: '40px' }}>
                    <div className="loading-spinner"></div>
                </div>
            </div>
        );
    }

    return (
        <div className="customer-parts-analysis">
            <h2>Parts Replacement Analysis</h2>

            <div className="parts-summary-stats">
                {summary && (
                    <>
                        <StatCard
                            icon={<FiBox color="#FF6900" size={24} />}
                            label="Unique Parts"
                            value={summary.uniquePartsCount.toString()}
                            trend={`Used across all customers`}
                        />
                        <StatCard
                            icon={<FiDollarSign color="#FF6900" size={24} />}
                            label="Total Parts Cost"
                            value={`$${summary.totalCost.toLocaleString()}`}
                            trend={`From ${summary.totalReplacements} replacements`}
                        />
                        <StatCard
                            icon={<FiRefreshCw color="#FF6900" size={24} />}
                            label="SRs With Parts"
                            value={summary.serviceRequestsWithParts.toString()}
                            trend={`${summary.serviceRequestsWithParts > 0
                                ? ((summary.serviceRequestsWithParts / 32449) * 100).toFixed(1)
                                : 0}% of total SRs`}
                        />
                    </>
                )}
            </div>

            {/* Customer Selection */}
            <div className="customer-selection">
                <label htmlFor="customer-select">Select Customer: </label>
                <select
                    id="customer-select"
                    value={selectedCustomer}
                    onChange={(e) => setSelectedCustomer(e.target.value)}
                    className="customer-select"
                    disabled={!hasData}
                >
                    <option value="">All Customers</option>
                    {customerOptions.map((customer, index) => (
                        <option key={index} value={customer.account}>
                            {customer.name} ({customer.count} SRs)
                        </option>
                    ))}
                </select>
            </div>

            {error && (
                <div className="error-message">
                    <FiAlertCircle size={20} />
                    <p>{error}</p>
                </div>
            )}

            {!hasData && !error ? (
                <div className="no-data-message">
                    <FiAlertCircle size={20} />
                    <p>No parts replacement data is available for the selected time period.</p>
                </div>
            ) : hasData && (
                <div className="parts-charts-container">
                    {/* Top Replaced Parts Chart - NOW WITH PART NUMBERS */}
                    <div className="chart-box">
                        <h3>Top Replaced Parts {selectedCustomer ? `for ${customerOptions.find(c => c.account === selectedCustomer)?.name || ''}` : ''}</h3>
                        <div className="parts-bar-chart">
                            <ResponsiveContainer width="100%" height={320}>
                                <BarChart
                                    data={topPartsData}
                                    margin={{ top: 20, right: 30, left: 20, bottom: 45 }}
                                >
                                    <CartesianGrid strokeDasharray="3 3" horizontal={true} vertical={false} />
                                    <XAxis
                                        dataKey="name" // This now contains part numbers
                                        tick={{ fill: '#666', fontSize: 11 }}
                                        angle={-45}
                                        textAnchor="end"
                                        height={45}
                                        tickMargin={2}
                                        interval={0}
                                    />
                                    <YAxis
                                        tickCount={5}
                                        axisLine={false}
                                        tickLine={false}
                                        label={{ value: 'Replacements', angle: -90, position: 'insideLeft', style: { textAnchor: 'middle' } }}
                                    />
                                    <Tooltip
                                        formatter={(value, name, props) => {
                                            const item = props.payload;
                                            return [
                                                <>
                                                    <div><strong>Part:</strong> {item.partNumber}</div>
                                                    <div><strong>Description:</strong> {item.partDescription}</div>
                                                    <div><strong>Replacements:</strong> {value}</div>
                                                    <div><strong>Cost:</strong> ${item.cost.toLocaleString()}</div>
                                                    {!selectedCustomer && <div><strong>Customer:</strong> {item.customer}</div>}
                                                </>,
                                                'Parts'
                                            ];
                                        }}
                                        labelStyle={{ color: '#333' }}
                                        contentStyle={{
                                            backgroundColor: 'white',
                                            border: '1px solid #e0e0e0',
                                            borderRadius: '4px',
                                            boxShadow: '0 2px 5px rgba(0,0,0,0.1)'
                                        }}
                                    />
                                    <Bar
                                        dataKey="count"
                                        radius={[4, 4, 0, 0]} // rounded top corners
                                    >
                                        {topPartsData.map((entry, index) => (
                                            <Cell key={`cell-${index}`} fill={entry.color} />
                                        ))}
                                    </Bar>
                                </BarChart>
                            </ResponsiveContainer>
                        </div>
                    </div>

                    {/* Parts Replacement Table */}
                    <div className="chart-box">
                        <h3>Parts Replacement Details</h3>
                        <div className="parts-table-container">
                            <table className="parts-table">
                                <thead>
                                    <tr>
                                        <th>Part Number</th>
                                        <th>Description</th>
                                        {!selectedCustomer && <th>Customer</th>}
                                        <th>Count</th>
                                        <th>Cost</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {partsData.slice(0, 12).map((part, index) => (
                                        <tr key={index}>
                                            <td>
                                                <div className="part-number-tag">{part.partNumber}</div>
                                            </td>
                                            <td>
                                                <div className="part-description-wrapper">
                                                    {part.partDescription || 'Unknown Part'}
                                                </div>
                                            </td>
                                            {!selectedCustomer && (
                                                <td>{part.customer}</td>
                                            )}
                                            <td>
                                                <div className="replacement-count-tag">{part.replacementCount}</div>
                                            </td>
                                            <td>${part.totalCost.toLocaleString()}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            )}

            {/* Machine Type Parts Analysis */}
            {machinePartsData.length > 0 && (
                <div className="chart-box mt-4">
                    <h3>Parts Replacement by Machine Type</h3>
                    <div className="machine-parts-table-container">
                        <table className="parts-table">
                            <thead>
                                <tr>
                                    <th>Machine Type</th>
                                    <th>Part Number</th>
                                    <th>Description</th>
                                    <th>Replacements</th>
                                    <th>Total Cost</th>
                                </tr>
                            </thead>
                            <tbody>
                                {machinePartsData.slice(0, 10).map((part, index) => (
                                    <tr key={index}>
                                        <td>
                                            <div className="machine-type-tag">{part.machineType}</div>
                                        </td>
                                        <td>
                                            <div className="part-number-tag">{part.partNumber}</div>
                                        </td>
                                        <td>
                                            <div className="part-description-wrapper">
                                                {part.partDescription || 'Unknown Part'}
                                            </div>
                                        </td>
                                        <td>{part.count}</td>
                                        <td>${part.cost.toLocaleString()}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}

            {/* Parts Data Debugger - only visible in development
            {process.env.NODE_ENV !== 'production' && (
                <PartsDataDebugger
                    partsData={{
                        customers: customerOptions,
                        partsData: partsData,
                        machinePartsData: machinePartsData,
                        summary: summary,
                        error: error
                    }}
                    dateFilters={dateFilters}
                />
            )} */}
        </div>
    );
};

export default CustomerPartsAnalysis;
