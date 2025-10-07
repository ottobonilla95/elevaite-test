"use client";

import React, { useState, useEffect } from 'react';
import { FiFileText, FiAlertTriangle, FiBarChart2, FiPackage, FiDollarSign, FiPieChart, FiAlertCircle } from 'react-icons/fi';

import './IssueCategories.scss';
import StatCard from '../SubComponents/StatCard';
import CustomPieChart from '../SubComponents/PieChart';
import ReverseBarChart from '../SubComponents/ReverseBarChart';
import Table, { Column } from '../SubComponents/Table';

import {
    fetchIssueStatistics,
    fetchIssueDistribution,
    fetchIssueCategories,
    fetchIssuesByMachineType,
    fetchIssuesByCustomer,
    fetchReplacedPartsOverview,
    fetchPartsToIssuesCorrelation
} from '../../lib/actions';

import {
    DateFilters,
    IssueStatistics,
    IssueCategoryData,
    CategoryBarData,
    MachineTypeIssue,
    CustomerTypeIssue,
    ReplacedPartsOverview,
    PartsIssueCorrelation
} from '../../lib/types';

interface IssueCategoriesProps {
    dateFilters: DateFilters;
}

const IssueCategories: React.FC<IssueCategoriesProps> = ({ dateFilters }) => {
    const [loading, setLoading] = useState(true);
    const [statistics, setStatistics] = useState<IssueStatistics | null>(null);
    const [distribution, setDistribution] = useState<IssueCategoryData[]>([]);
    const [categories, setCategories] = useState<CategoryBarData[]>([]);
    const [machineIssues, setMachineIssues] = useState<MachineTypeIssue[]>([]);
    const [customerIssues, setCustomerIssues] = useState<CustomerTypeIssue[]>([]);
    const [partsOverview, setPartsOverview] = useState<ReplacedPartsOverview | null>(null);
    const [correlation, setCorrelation] = useState<PartsIssueCorrelation[]>([]);
    const [selectedTab, setSelectedTab] = useState<'machine' | 'customer'>('machine');
    const [tableData, setTableData] = useState<any[]>([]);

    // API error tracking
    const [apiErrors, setApiErrors] = useState<{ [key: string]: string }>({});
    const [dataLoaded, setDataLoaded] = useState(false);

    useEffect(() => {
        loadData();
    }, [dateFilters]);

    useEffect(() => {
        // Update table data when tab selection changes
        if (selectedTab === 'machine') {
            setTableData(machineIssues);
        } else {
            setTableData(customerIssues);
        }
    }, [selectedTab, machineIssues, customerIssues]);

    const loadData = async () => {
        try {
            setLoading(true);
            setApiErrors({});
            console.log("Loading issue data with filters:", dateFilters);

            const filters = {
                start_date: dateFilters.start_date,
                end_date: dateFilters.end_date
            };

            // Use Promise.allSettled to handle failing API calls gracefully
            const results = await Promise.allSettled([
                fetchIssueStatistics(filters).catch(err => {
                    console.error("Error in fetchIssueStatistics:", err);
                    return null;
                }),
                fetchIssueDistribution(filters).catch(err => {
                    console.error("Error in fetchIssueDistribution:", err);
                    return [];
                }),
                fetchIssueCategories(filters).catch(err => {
                    console.error("Error in fetchIssueCategories:", err);
                    return [];
                }),
                fetchIssuesByMachineType(filters).catch(err => {
                    console.error("Error in fetchIssuesByMachineType:", err);
                    return [];
                }),
                fetchIssuesByCustomer(filters).catch(err => {
                    console.error("Error in fetchIssuesByCustomer:", err);
                    return [];
                }),
                fetchReplacedPartsOverview(filters).catch(err => {
                    console.error("Error in fetchReplacedPartsOverview:", err);
                    return null;
                }),
                fetchPartsToIssuesCorrelation(filters).catch(err => {
                    console.error("Error in fetchPartsToIssuesCorrelation:", err);
                    return [];
                })
            ]);

            const newErrors: { [key: string]: string } = {};

            // Process issue statistics result
            if (results[0].status === 'fulfilled' && results[0].value) {
                console.log("Issue statistics loaded:", results[0].value);
                setStatistics(results[0].value);
            } else {
                console.error("Error loading issue statistics:",
                    results[0].status === 'rejected' ? results[0].reason : 'Empty response');
                newErrors.statistics = "Failed to load issue statistics";
            }

            // Process issue distribution result
            if (results[1].status === 'fulfilled' && results[1].value && results[1].value.length > 0) {
                console.log("Issue distribution loaded:", results[1].value);
                setDistribution(results[1].value);
            } else {
                console.error("Error loading issue distribution:",
                    results[1].status === 'rejected' ? results[1].reason : 'Empty response');
                newErrors.distribution = "Failed to load issue distribution";
            }

            // Process issue categories result
            if (results[2].status === 'fulfilled' && results[2].value && results[2].value.length > 0) {
                console.log("Issue categories loaded:", results[2].value);
                setCategories(results[2].value);
            } else {
                console.error("Error loading issue categories:",
                    results[2].status === 'rejected' ? results[2].reason : 'Empty response');
                newErrors.categories = "Failed to load issue categories";
            }

            // Process machine issues result
            if (results[3].status === 'fulfilled' && results[3].value && results[3].value.length > 0) {
                console.log("Machine issues loaded:", results[3].value);
                setMachineIssues(results[3].value);
            } else {
                console.error("Error loading machine issues:",
                    results[3].status === 'rejected' ? results[3].reason : 'Empty response');
                newErrors.machineIssues = "Failed to load machine issues";
            }

            // Process customer issues result
            if (results[4].status === 'fulfilled' && results[4].value && results[4].value.length > 0) {
                console.log("Customer issues loaded:", results[4].value);
                setCustomerIssues(results[4].value);
            } else {
                console.error("Error loading customer issues:",
                    results[4].status === 'rejected' ? results[4].reason : 'Empty response');
                newErrors.customerIssues = "Failed to load customer issues";
            }

            // Process parts overview result
            if (results[5].status === 'fulfilled' && results[5].value) {
                console.log("Parts overview loaded:", results[5].value);
                setPartsOverview(results[5].value);
            } else {
                console.error("Error loading parts overview:",
                    results[5].status === 'rejected' ? results[5].reason : 'Empty response');
                newErrors.partsOverview = "Failed to load parts overview";
            }

            if (results[6].status === 'fulfilled' && results[6].value && results[6].value.length > 0) {
                console.log("Parts correlation loaded:", results[6].value);
                setCorrelation(results[6].value);
            } else {
                console.error("Error loading parts correlation:",
                    results[6].status === 'rejected' ? results[6].reason : 'Empty response');
                newErrors.correlation = "Failed to load parts correlation";
            }

            setApiErrors(newErrors);
            setTableData(selectedTab === 'machine' ? machineIssues : customerIssues);

            setDataLoaded(true);
        } catch (error) {
            console.error("Error loading issue data:", error);
            setApiErrors({
                statistics: "Failed to load any data",
                distribution: "Failed to load any data",
                categories: "Failed to load any data",
                machineIssues: "Failed to load any data",
                customerIssues: "Failed to load any data"
            });
            setDataLoaded(true);
        } finally {
            setLoading(false);
        }
    };

    const handleButtonClick = (dataType: 'customer' | 'machine') => {
        setSelectedTab(dataType);
    };

    const renderErrorIndicator = (dataSource: string) => {
        if (apiErrors[dataSource]) {
            return (
                <div className="api-error-indicator">
                    <FiAlertCircle color="#EF4444" size={16} />
                    <span>Using demo data</span>
                </div>
            );
        }
        return null;
    };

    const MachineTypeColumns: Column<MachineTypeIssue>[] = [
        {
            label: "Machine Type",
            key: "machineType",
            render: (value) => <span className="part-number">{value}</span>,
        },
        { label: "Most Common Issue", key: "mostCommonIssue" },
        {
            label: "Occurrences",
            key: "occurnces",
            render: (value) => `${value}`,
        },
        {
            label: "Most Replaced Part Description",
            key: "mostReplacedPart",
            render: (value, row) => (
                <div>
                    <span className="part-description">{value || "N/A"}</span>
                    {row.partCount && row.partCount > 0 && <div className="part-count">{row.partCount} replacements</div>}
                </div>
            ),
        },
        {
            label: "% Of Type's Issues",
            key: "percentage",
            render: (value) => <span className="tag">{value}%</span>,
        }
    ];

    const customerTypeColumns: Column<CustomerTypeIssue>[] = [
        {
            label: "Customer",
            key: "customerType",
            render: (value) => <span className="part-number">{value}</span>,
        },
        { label: "Most Common Issue", key: "mostCommonIssue" },
        {
            label: "Occurrences",
            key: "occurnces",
            render: (value) => `${value}`,
        },
        {
            label: "Most Replaced Part Description",
            key: "mostReplacedPart",
            render: (value, row) => (
                <div>
                    <span className="part-description">{value || "N/A"}</span>
                    {row.partCost && row.partCost > 0 && <div className="part-cost">${row.partCost.toLocaleString()}</div>}
                </div>
            ),
        },
        {
            label: "% Of Type's Issues",
            key: "percentage",
            render: (value) => <span className="tag">{value}%</span>,
        }
    ];

    const statCardData = [
        {
            icon: <FiFileText color="#FF6900" size={24} />,
            label: "Total Service Requests",
            value: statistics ? statistics.totalIssues.toLocaleString() : "0",
            trend: undefined,
        },
        {
            icon: <FiAlertTriangle color="#FF6900" size={24} />,
            label: "Most Common Issue",
            value: statistics?.mostCommonIssue?.issue || "N/A",
            trend: statistics?.mostCommonIssue?.count && statistics.mostCommonIssue.count > 0
                ? `${statistics.mostCommonIssue.count.toLocaleString()} occurrences · ${statistics.mostCommonIssue.percentage}%`
                : "No data available",
        },
        {
            icon: <FiPackage color="#FF6900" size={24} />,
            label: "Most Replaced Part Description",
            value: statistics?.mostReplacedPart?.description || "N/A",
            trend: statistics?.mostReplacedPart?.count && statistics.mostReplacedPart.count > 0
                ? `${statistics.mostReplacedPart.count.toLocaleString()} replacements · $${statistics.mostReplacedPart.cost.toLocaleString()}`
                : "No data available",
        }
    ];

    const renderPartsOverview = () => {
        if (!partsOverview || !partsOverview.topReplacedParts || partsOverview.topReplacedParts.length === 0) {
            return (
                <div className="no-data-message">
                    No parts replacement data available
                </div>
            );
        }

        return (
            <div className="parts-overview-content">
                <div className="parts-overview-summary">
                    <StatCard
                        icon={<FiPackage color="#FF6900" size={24} />}
                        label="Unique Parts"
                        value={partsOverview.summary.uniquePartsCount.toLocaleString()}
                    />
                    <StatCard
                        icon={<FiDollarSign color="#FF6900" size={24} />}
                        label="Total Parts Cost"
                        value={`$${partsOverview.summary.totalCost.toLocaleString()}`}
                    />
                    <StatCard
                        icon={<FiBarChart2 color="#FF6900" size={24} />}
                        label="Service Requests With Parts"
                        value={partsOverview.summary.affectedServiceRequests.toLocaleString()}
                        trend={`${partsOverview.summary.percentRequiringParts}% of all service requests`}
                    />
                </div>
                <div className="parts-cards">
                    {partsOverview.topReplacedParts.slice(0, 5).map((part, index) => (
                        <div key={index} className="parts-card">
                            <div className="part-header">
                                <span className="part-number">{part.partNumber}</span>
                                <span className="part-cost">${part.totalCost.toLocaleString()}</span>
                            </div>
                            <div className="part-description">{part.description}</div>
                            <div className="part-details">
                                <span><FiBarChart2 size={14} /> {part.replacementCount} replacements</span>
                                <span><FiFileText size={14} /> {part.serviceRequests} service requests</span>
                                <span><FiPieChart size={14} /> {part.machineTypes} machine types</span>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        );
    };

    const renderCorrelation = () => {
        if (!correlation || correlation.length === 0) {
            return (
                <div className="no-data-message">
                    No correlation data available
                </div>
            );
        }

        return (
            <table className="correlation-table">
                <thead>
                    <tr>
                        <th>Issue</th>
                        <th>Replaced Part</th>
                        <th>Occurrence Count</th>
                    </tr>
                </thead>
                <tbody>
                    {correlation.slice(0, 10).map((item, index) => (
                        <tr key={index}>
                            <td>{item.issue}</td>
                            <td>{item.partDescription}</td>
                            <td>{item.occurrenceCount}</td>
                        </tr>
                    ))}
                </tbody>
            </table>
        );
    };

    if (loading && !dataLoaded) {
        return <div className='issue-category-container'>Loading issue category data...</div>;
    }

    return (
        <div className='issue-category-container'>
            {process.env.NODE_ENV === 'development' && Object.keys(apiErrors).length > 0 && (
                <div style={{
                    padding: '10px',
                    background: '#fff3cd',
                    border: '1px solid #ffeeba',
                    borderRadius: '4px',
                    marginBottom: '16px',
                    fontSize: '13px'
                }}>
                    <p style={{ fontWeight: 'bold', marginBottom: '5px' }}>
                        <FiAlertCircle style={{ marginRight: '5px' }} />
                        Backend SQL Errors Detected
                    </p>
                    <p>SQL errors in backend. Using demo data for visualization until SQL errors are fixed.</p>
                    <ul style={{ margin: '5px 0', paddingLeft: '20px' }}>
                        {Object.entries(apiErrors).map(([key, value]) => (
                            <li key={key}>{key}: {value}</li>
                        ))}
                    </ul>
                </div>
            )}

            <div className="issue-statistics-container">
                <h2><b>Key Statistics</b></h2>
                {renderErrorIndicator('statistics')}
                <div className="issue-statistics-tab">
                    {statCardData.map((card, index) => (
                        <StatCard
                            key={index}
                            icon={card.icon}
                            label={card.label}
                            value={card.value}
                            trend={card.trend}
                        />
                    ))}
                </div>
            </div>

            <div className='issue-panel-container'>
                <div className='issue-panel-header'>
                    <h2><b>Issues Panel</b></h2>
                    <select className='project-dropdown'>
                        <option>All Projects</option>
                    </select>
                </div>
                <div className='issue-panel-charts'>
                    <div className="charts-box">
                        <h4>Issues Distribution</h4>
                        {renderErrorIndicator('distribution')}
                        <div className="chart-wrapper">
                            <CustomPieChart data={distribution.slice(0, 6)} dollorValue={false} />
                        </div>
                    </div>
                    <div className="charts-box">
                        <h4>Issues by Category</h4>
                        {renderErrorIndicator('categories')}
                        <div className="chart-wrapper">
                            <ReverseBarChart data={categories} />
                        </div>
                    </div>
                </div>
            </div>

            <div className='issue-table-container'>
                <h2><b>Most Common Issues</b></h2>
                <div className="button-switch-container">
                    <button
                        className={selectedTab === 'customer' ? 'switch-button active' : 'switch-button'}
                        onClick={() => handleButtonClick('customer')}
                    >
                        by Top Customer
                    </button>
                    <button
                        className={selectedTab === 'machine' ? 'switch-button active' : 'switch-button'}
                        onClick={() => handleButtonClick('machine')}
                    >
                        by Machine Type
                    </button>
                </div>
                {renderErrorIndicator(selectedTab === 'machine' ? 'machineIssues' : 'customerIssues')}
                <Table
                    title="Most Common Issues"
                    data={tableData}
                    showExportButton={false}
                    columns={selectedTab === 'machine' ? MachineTypeColumns : customerTypeColumns as any}
                    showPagination={false}
                />
            </div>

            <div className='parts-overview-container'>
                <h2><b>Parts Replacement Analysis</b></h2>
                {renderErrorIndicator('partsOverview')}
                {renderPartsOverview()}
            </div>

            <div className='parts-overview-container'>
                <h2><b>Issue-Part Correlation</b></h2>
                {renderErrorIndicator('correlation')}
                {renderCorrelation()}
            </div>
        </div>
    );
};

export default IssueCategories;
