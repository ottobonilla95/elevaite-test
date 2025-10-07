import React, { useEffect, useState } from 'react';
import { FiUsers, FiPieChart, FiBarChart, FiPackage, FiSettings, FiUser, FiChevronDown, FiFilter } from 'react-icons/fi';
import './CustomerAnalytics.scss';

import {
    fetchTopCustomers,
    fetchCustomerDistribution,
    fetchCustomerParts,
    fetchServiceMetrics,
    fetchServiceMachineDistribution,
    fetchCustomerDetailedMetrics,
    fetchCustomerTopTechnicians
} from '../../lib/actions';
import {
    CustomerData,
    CustomerProportion
} from '../../lib/types';
import { DateFilters } from '../Tabs';

interface ManagerFilter {
    managerId: number | null;
    managerName: string;
}

interface FSTFilter {
    fstId: number | null;
    fstName: string;
}

interface CustomerAnalyticsProps {
    dateFilters: DateFilters;
    managerFilter?: ManagerFilter;
    fstFilter?: FSTFilter;
}

const CustomerAnalytics: React.FC<CustomerAnalyticsProps> = ({
    dateFilters,
    managerFilter,
    fstFilter
}) => {
    const [loading, setLoading] = useState(true);
    const [selectedCustomer, setSelectedCustomer] = useState('');
    const [topCustomers, setTopCustomers] = useState<CustomerData[]>([]);
    const [distribution, setDistribution] = useState<CustomerProportion[]>([]);

    const [customerParts, setCustomerParts] = useState<any>(null);
    const [customerMachines, setCustomerMachines] = useState<any[]>([]);
    const [customerMetrics, setCustomerMetrics] = useState<any>(null);
    const [customerDetailedMetrics, setCustomerDetailedMetrics] = useState<any>(null);
    const [loadingCustomerData, setLoadingCustomerData] = useState(false);

    const [hoveredSlice, setHoveredSlice] = useState<number | null>(null);

    const [showAllCustomers, setShowAllCustomers] = useState(false);
    const [displayCount, setDisplayCount] = useState(15);
    const [topTechnicians, setTopTechnicians] = useState<any[]>([]);

    useEffect(() => {
        loadData();
    }, [dateFilters, managerFilter, fstFilter]);

    useEffect(() => {
        if (selectedCustomer) {
            loadCustomerSpecificData();
        }
    }, [selectedCustomer, dateFilters, managerFilter, fstFilter]);

    const loadData = async () => {
        try {
            setLoading(true);

            console.log('🔍 CustomerAnalytics - Raw props received:');
            console.log('  - dateFilters:', dateFilters);
            console.log('  - managerFilter:', managerFilter);
            console.log('  - fstFilter:', fstFilter);

            const filters = {
                start_date: dateFilters.startDate || undefined,
                end_date: dateFilters.endDate || undefined,
                manager_id: managerFilter?.managerId || undefined,
                fst_id: fstFilter?.fstId || undefined
            };

            console.log(' Customer Analytics - Built filters object:', filters);
            console.log(' Filter values check:');
            console.log(`  - manager_id: ${filters.manager_id} (type: ${typeof filters.manager_id})`);
            console.log(`  - fst_id: ${filters.fst_id} (type: ${typeof filters.fst_id})`);
            console.log(`  - start_date: ${filters.start_date}`);
            console.log(`  - end_date: ${filters.end_date}`);

            const [customers, customerDist] = await Promise.all([
                fetchTopCustomers(filters),
                fetchCustomerDistribution(filters)
            ]);

            setTopCustomers(customers);
            setDistribution(customerDist);

            console.log(`Loaded ${customers.length} customers with filters: manager_id=${filters.manager_id}, fst_id=${filters.fst_id}, dates=${filters.start_date || 'all'} to ${filters.end_date || 'all'}`);
        } catch (error) {
            console.error(" Error loading customer data:", error);
        } finally {
            setLoading(false);
        }
    };

    const loadCustomerSpecificData = async () => {
        if (!selectedCustomer) return;

        try {
            setLoadingCustomerData(true);

            // Find the customer object to get the account number
            const customer = topCustomers.find(c => c.customer === selectedCustomer);
            if (!customer) {
                console.error('Customer not found in topCustomers list:', selectedCustomer);
                return;
            }

            const customerAccount = customer.customerAccount;
            console.log(`🔍 Loading data for customer: ${selectedCustomer} (Account: ${customerAccount})`);
            console.log('🔍 Customer object:', customer);

            const filters = {
                start_date: (dateFilters.startDate && dateFilters.startDate.trim() !== '') ? dateFilters.startDate : undefined,
                end_date: (dateFilters.endDate && dateFilters.endDate.trim() !== '') ? dateFilters.endDate : undefined,
                customer: selectedCustomer,
                customer_account: customerAccount, // Make sure this is passed
                manager_id: managerFilter?.managerId || undefined,
                fst_id: fstFilter?.fstId || undefined
            };

            console.log('🔍 Customer Analytics - Loading customer-specific data with filters:', filters);

            // Make sure we're passing the customerAccount to all API calls
            const [partsData, machineData, metricsData, detailedMetrics, topTechnicians] = await Promise.all([
                fetchCustomerParts({
                    start_date: filters.start_date,
                    end_date: filters.end_date,
                    customer_account: customerAccount,
                    manager_id: filters.manager_id,
                    fst_id: filters.fst_id
                }).catch((error) => {
                    console.error('Error fetching customer parts:', error);
                    return null;
                }),
                fetchServiceMachineDistribution({
                    start_date: filters.start_date,
                    end_date: filters.end_date,
                    customer: selectedCustomer, // Use customer name for this API
                    manager_id: filters.manager_id,
                    fst_id: filters.fst_id
                }).catch((error) => {
                    console.error('Error fetching machine distribution:', error);
                    return [];
                }),
                fetchServiceMetrics({
                    start_date: filters.start_date,
                    end_date: filters.end_date,
                    customer: selectedCustomer, // Use customer name for this API
                    manager_id: filters.manager_id,
                    fst_id: filters.fst_id
                }).catch((error) => {
                    console.error('Error fetching service metrics:', error);
                    return null;
                }),
                fetchCustomerDetailedMetrics({
                    start_date: filters.start_date,
                    end_date: filters.end_date,
                    customer_account: customerAccount || '', // Use account number for detailed metrics
                    manager_id: filters.manager_id,
                    fst_id: filters.fst_id
                }).catch((error) => {
                    console.error('Error fetching detailed metrics:', error);
                    return null;
                }),
                fetchCustomerTopTechnicians({
                    start_date: filters.start_date,
                    end_date: filters.end_date,
                    customer_account: customerAccount || '',
                    manager_id: filters.manager_id,
                    fst_id: filters.fst_id
                }).catch((error) => {
                    console.error('Error fetching top technicians:', error);
                    return { top_technicians: [] };
                })
            ]);

            setCustomerParts(partsData);
            setCustomerMachines(machineData || []);
            setCustomerMetrics(metricsData);
            setCustomerDetailedMetrics(detailedMetrics);
            setTopTechnicians(topTechnicians?.top_technicians || []);

            console.log('Customer-specific data loaded for:', selectedCustomer);
            console.log('Parts data:', partsData);
            console.log('Detailed metrics:', detailedMetrics);

        } catch (error) {
            console.error("Error loading customer-specific data:", error);
        } finally {
            setLoadingCustomerData(false);
        }
    };


    const renderEnhancedPieChart = () => {
        if (!distribution || distribution.length === 0) {
            return <div className="no-data">No distribution data available</div>;
        }

        const radius = 90;
        const centerX = 200;
        const centerY = 150;
        let cumulativePercentage = 0;

        return (
            <div className="enhanced-pie-chart">
                <div className="pie-chart-wrapper">
                    <svg width="400" height="300" viewBox="0 0 400 300">
                        <defs>
                            <filter id="shadow" x="-50%" y="-50%" width="200%" height="200%">
                                <feDropShadow dx="2" dy="4" stdDeviation="3" floodOpacity="0.3" />
                            </filter>
                            <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
                                <feGaussianBlur stdDeviation="4" result="coloredBlur" />
                                <feMerge>
                                    <feMergeNode in="coloredBlur" />
                                    <feMergeNode in="SourceGraphic" />
                                </feMerge>
                            </filter>
                        </defs>

                        <g transform={`translate(${centerX}, ${centerY})`}>
                            {distribution.slice(0, 5).map((item, index) => {
                                const percentage = item.value;
                                const startAngle = (cumulativePercentage / 100) * 360 - 90;
                                const endAngle = ((cumulativePercentage + percentage) / 100) * 360 - 90;

                                const isHovered = hoveredSlice === index;
                                const currentRadius = isHovered ? radius + 10 : radius;

                                const startAngleRad = (startAngle * Math.PI) / 180;
                                const endAngleRad = (endAngle * Math.PI) / 180;

                                const x1 = currentRadius * Math.cos(startAngleRad);
                                const y1 = currentRadius * Math.sin(startAngleRad);
                                const x2 = currentRadius * Math.cos(endAngleRad);
                                const y2 = currentRadius * Math.sin(endAngleRad);

                                const largeArcFlag = percentage > 50 ? 1 : 0;

                                const pathData = [
                                    'M 0 0',
                                    `L ${x1} ${y1}`,
                                    `A ${currentRadius} ${currentRadius} 0 ${largeArcFlag} 1 ${x2} ${y2}`,
                                    'Z'
                                ].join(' ');

                                cumulativePercentage += percentage;

                                return (
                                    <g key={index}>
                                        <path
                                            d={pathData}
                                            fill={item.color || `hsl(${25 + index * 45}, 70%, ${60 - index * 5}%)`}
                                            stroke="white"
                                            strokeWidth="3"
                                            filter={isHovered ? "url(#glow)" : "url(#shadow)"}
                                            style={{
                                                cursor: 'pointer',
                                                transition: 'all 0.3s ease',
                                                opacity: isHovered ? 1 : 0.9
                                            }}
                                            onMouseEnter={() => setHoveredSlice(index)}
                                            onMouseLeave={() => setHoveredSlice(null)}
                                        />
                                        {isHovered && (
                                            <text
                                                x={0}
                                                y={0}
                                                textAnchor="middle"
                                                dominantBaseline="middle"
                                                fill="white"
                                                fontSize="16"
                                                fontWeight="bold"
                                                style={{ pointerEvents: 'none' }}
                                            >
                                                {percentage}%
                                            </text>
                                        )}
                                    </g>
                                );
                            })}

                            <circle
                                cx="0"
                                cy="0"
                                r="30"
                                fill="white"
                                stroke="#e2e8f0"
                                strokeWidth="2"
                                filter="url(#shadow)"
                            />
                            <text
                                x="0"
                                y="0"
                                textAnchor="middle"
                                dominantBaseline="middle"
                                fill="#64748b"
                                fontSize="12"
                                fontWeight="600"
                            >
                                Total
                            </text>
                        </g>
                    </svg>
                </div>

                <div className="enhanced-pie-legend">
                    {distribution.slice(0, 5).map((item, index) => (
                        <div
                            key={index}
                            className={`legend-item ${hoveredSlice === index ? 'hovered' : ''}`}
                            onMouseEnter={() => setHoveredSlice(index)}
                            onMouseLeave={() => setHoveredSlice(null)}
                        >
                            <div
                                className="legend-color"
                                style={{ backgroundColor: item.color || `hsl(${25 + index * 45}, 70%, ${60 - index * 5}%)` }}
                            />
                            <div className="legend-details">
                                <span className="legend-label">{item.name}</span>
                                <div className="legend-metrics">
                                    <span className="legend-percentage">{item.value}%</span>
                                    <span className="legend-count">{item.count} SRs</span>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        );
    };

    if (loading) {
        return (
            <div className='customer-analytics-container'>
                <div className="loading-state">
                    <div className="loading-spinner"></div>
                    <p>Loading customer analytics...</p>
                </div>
            </div>
        );
    }

    if (topCustomers.length === 0) {
        return (
            <div className='customer-analytics-container'>
                <div className="no-data-state">
                    <FiUsers size={48} color="#ccc" />
                    <p>No customer data available for the selected filters</p>
                    {(dateFilters.startDate || dateFilters.endDate || managerFilter?.managerId || fstFilter?.fstId) && (
                        <small>Try expanding your date range or removing filters</small>
                    )}
                </div>
            </div>
        );
    }

    const maxValue = Math.max(...topCustomers.slice(0, 10).map(c => c.serviceRequests));
    const barHeight = 20;

    const customersToShow = showAllCustomers ? topCustomers : topCustomers.slice(0, displayCount);

    const getDateRangeText = () => {
        if (!dateFilters.startDate && !dateFilters.endDate) {
            return "All Time Data";
        }
        if (dateFilters.startDate && dateFilters.endDate) {
            return `${dateFilters.startDate} to ${dateFilters.endDate}`;
        }
        if (dateFilters.startDate) {
            return `From ${dateFilters.startDate}`;
        }
        if (dateFilters.endDate) {
            return `Until ${dateFilters.endDate}`;
        }
        return "All Time Data";
    };

    return (
        <div className='customer-analytics-container'>
            {/* Filter Status Bar */}
            {(managerFilter?.managerId || fstFilter?.fstId) && (
                <div className="filter-status-bar">
                    <div className="filter-info">
                        <FiFilter className="filter-icon" />
                        <span>
                            {fstFilter?.fstId
                                ? `Showing data for FST: ${fstFilter.fstName}`
                                : managerFilter?.managerId
                                    ? `Showing data for Manager: ${managerFilter.managerName}'s team`
                                    : 'Filter applied'
                            }
                        </span>
                    </div>
                </div>
            )}

            {/* DEBUG */}
            {/* <div style={{
                backgroundColor: '#f0f0f0',
                padding: '10px',
                margin: '10px 0',
                borderRadius: '4px',
                fontSize: '12px',
                fontFamily: 'monospace'
            }}>
                <strong>🔧 DEBUG INFO:</strong><br />
                Manager ID: {managerFilter?.managerId} | FST ID: {fstFilter?.fstId}<br />
                Date: {dateFilters.startDate} to {dateFilters.endDate}
            </div> */}

            <div className='customer-selection-card'>
                <div className="selection-header">
                    <h3>Customer Analysis</h3>
                    <p>Select a specific customer for detailed analysis or view all customers</p>
                </div>
                <select
                    value={selectedCustomer}
                    onChange={(e) => setSelectedCustomer(e.target.value)}
                    className="customer-select"
                >
                    <option value="">All Customers Overview</option>
                    {topCustomers.map((customer, index) => (
                        <option key={index} value={customer.customer}>
                            {customer.customer} ({customer.serviceRequests} SRs)
                        </option>
                    ))}
                </select>
            </div>

            <div className="analytics-grid">
                <div className='chart-card bar-chart-card'>
                    <div className="card-header">
                        <div className="header-with-icon">
                            <FiBarChart className="card-icon" />
                            <div>
                                <h3>Service Requests by Customer</h3>
                                <p>Number of service requests per customer</p>
                            </div>
                        </div>
                    </div>
                    <div className="chart-container">
                        <div className="custom-bar-chart">
                            {topCustomers.slice(0, 8).map((customer, index) => (
                                <div key={index} className="bar-item">
                                    <div className="bar-label">
                                        <span className="customer-name" title={customer.customer}>
                                            {customer.customer.length > 20 ?
                                                customer.customer.substring(0, 20) + '...' :
                                                customer.customer
                                            }
                                        </span>
                                        <span className="customer-value">{customer.serviceRequests}</span>
                                    </div>
                                    <div className="bar-container">
                                        <div
                                            className="bar-fill"
                                            style={{
                                                width: `${(customer.serviceRequests / maxValue) * 100}%`,
                                                height: `${barHeight}px`
                                            }}
                                        />
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>

                <div className='chart-card pie-chart-card'>
                    <div className="card-header">
                        <div className="header-with-icon">
                            <FiPieChart className="card-icon" />
                            <div>
                                <h3>Customer Distribution</h3>
                                <p>Proportion of total service requests </p>
                            </div>
                        </div>
                    </div>
                    <div className="chart-container">
                        {renderEnhancedPieChart()}
                    </div>
                </div>
            </div>

            <div className='table-card'>
                <div className="table-header-with-controls">
                    <div className="card-header">
                        <h3>All Customers Summary</h3>
                        <p>Complete list of customers with service request metrics and resolution times</p>
                    </div>
                    <div className="table-controls">
                        <div className="display-options">
                            <button
                                className={`display-btn ${!showAllCustomers ? 'active' : ''}`}
                                onClick={() => setShowAllCustomers(false)}
                            >
                                Top {displayCount}
                            </button>
                            <button
                                className={`display-btn ${showAllCustomers ? 'active' : ''}`}
                                onClick={() => setShowAllCustomers(true)}
                            >
                                All Customers ({topCustomers.length})
                            </button>
                        </div>

                        {!showAllCustomers && (
                            <div className="count-selector">
                                <label htmlFor="display-count">Show:</label>
                                <select
                                    id="display-count"
                                    value={displayCount}
                                    onChange={(e) => setDisplayCount(Number(e.target.value))}
                                    className="count-select"
                                >
                                    <option value={10}>Top 10</option>
                                    <option value={15}>Top 15</option>
                                    <option value={25}>Top 25</option>
                                    <option value={50}>Top 50</option>
                                </select>
                            </div>
                        )}
                    </div>
                </div>

                <div className="table-container">
                    <table className="summary-table">
                        <thead>
                            <tr>
                                <th>Rank</th>
                                <th>Customer</th>
                                <th># Service Requests</th>
                                <th>% of Total SR</th>
                                <th>Avg Resolution Time</th>
                            </tr>
                        </thead>
                        <tbody>
                            {customersToShow.map((customer, index) => (
                                <tr key={index}>
                                    <td>
                                        <div className="rank-badge">#{index + 1}</div>
                                    </td>
                                    <td>
                                        <div className="customer-cell">
                                            <div className="customer-avatar">
                                                {customer.customer.charAt(0).toUpperCase()}
                                            </div>
                                            <span className="customer-name">{customer.customer}</span>
                                        </div>
                                    </td>
                                    <td>
                                        <span className="metric-value">{customer.serviceRequests.toLocaleString()}</span>
                                    </td>
                                    <td>
                                        <div className="percentage-badge">{customer.percentTotal}</div>
                                    </td>
                                    <td>
                                        <span className="time-value">{customer.avgResolutionTime}</span>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>

                {!showAllCustomers && topCustomers.length > displayCount && (
                    <div className="table-footer">
                        <button
                            className="show-all-btn"
                            onClick={() => setShowAllCustomers(true)}
                        >
                            <FiChevronDown size={16} />
                            Show All {topCustomers.length} Customers
                        </button>
                    </div>
                )}
            </div>

            {selectedCustomer && (
                <div className='selected-customer-section'>
                    <div className="customer-details-card">
                        <div className="customer-header">
                            <div className="customer-avatar large">
                                {selectedCustomer.charAt(0).toUpperCase()}
                            </div>
                            <div className="customer-info">
                                <h2>{selectedCustomer}</h2>
                                <p>Detailed customer analysis and metrics for {getDateRangeText()}</p>
                                {(managerFilter?.managerId || fstFilter?.fstId) && (
                                    <small>
                                        Filtered by: {fstFilter?.fstName || `${managerFilter?.managerName}'s team`}
                                    </small>
                                )}
                            </div>
                        </div>

                        <div className="customer-metrics">
                            {customerDetailedMetrics ? (
                                <div className="enhanced-metrics-grid">
                                    <div className="metric-item">
                                        <span className="metric-label">Service Requests</span>
                                        <span className="metric-value large">{customerDetailedMetrics.serviceRequests?.total || 0}</span>
                                        <span className="metric-detail">{customerDetailedMetrics.serviceRequests?.resolved || 0} resolved, {customerDetailedMetrics.serviceRequests?.open || 0} open</span>
                                    </div>
                                    <div className="metric-item">
                                        <span className="metric-label">Resolution Rate</span>
                                        <span className="metric-value">{customerDetailedMetrics.serviceRequests?.resolutionRate || 0}%</span>
                                        <span className="metric-detail">Completion rate</span>
                                    </div>
                                    <div className="metric-item">
                                        <span className="metric-label">Avg Resolution Time</span>
                                        <span className="metric-value">{customerDetailedMetrics.performance?.avgResolutionDays || 0} days</span>
                                        <span className="metric-detail">Customer-specific</span>
                                    </div>
                                    <div className="metric-item">
                                        <span className="metric-label">Total Parts Cost</span>
                                        <span className="metric-value">${customerDetailedMetrics.resources?.totalPartsCost?.toLocaleString() || 0}</span>
                                        <span className="metric-detail">{customerDetailedMetrics.resources?.uniquePartsUsed || 0} unique parts</span>
                                    </div>
                                </div>
                            ) : (
                                (() => {
                                    const customer = topCustomers.find(c => c.customer === selectedCustomer);
                                    return customer ? (
                                        <div className="metrics-grid">
                                            <div className="metric-item">
                                                <span className="metric-label">Service Requests</span>
                                                <span className="metric-value large">{customer.serviceRequests}</span>
                                            </div>
                                            <div className="metric-item">
                                                <span className="metric-label">% of Total</span>
                                                <span className="metric-value">{customer.percentTotal}</span>
                                            </div>
                                            <div className="metric-item">
                                                <span className="metric-label">Avg Resolution</span>
                                                <span className="metric-value">{customer.avgResolutionTime}</span>
                                            </div>
                                        </div>
                                    ) : null;
                                })()
                            )}
                        </div>
                    </div>

                    <div className="customer-specific-analysis">
                        <h3>Customer-Specific Analysis</h3>

                        {loadingCustomerData ? (
                            <div className="loading-customer-data">
                                <div className="loading-spinner"></div>
                                <p>Loading detailed analysis for {selectedCustomer}...</p>
                            </div>
                        ) : (
                            <div className="analysis-grid">
                                <div className="analysis-card">
                                    <div className="card-header">
                                        <FiPackage className="card-icon" />
                                        <div>
                                            <h4>Parts Ordered and Total Cost</h4>
                                            <p>Parts data for this customer</p>
                                        </div>
                                    </div>
                                    <div className="card-content">
                                        {customerParts && customerParts.summary ? (
                                            <div className="parts-summary">
                                                <div className="metric-row">
                                                    <span className="metric-label">Unique Parts:</span>
                                                    <span className="metric-value">{customerParts.summary.uniquePartsCount}</span>
                                                </div>
                                                <div className="metric-row">
                                                    <span className="metric-label">Total Cost:</span>
                                                    <span className="metric-value">${customerParts.summary.totalCost.toLocaleString()}</span>
                                                </div>
                                                <div className="metric-row">
                                                    <span className="metric-label">Total Replacements:</span>
                                                    <span className="metric-value">{customerParts.summary.totalReplacements}</span>
                                                </div>
                                                {customerParts.partsData && customerParts.partsData.length > 0 && (
                                                    <div className="top-parts">
                                                        <h5>Top 5 Parts:</h5>
                                                        {customerParts.partsData.slice(0, 5).map((part: any, index: number) => (
                                                            <div key={index} className="part-item">
                                                                <div className="part-info">
                                                                    <span className="part-number">{part.partNumber}</span>
                                                                    <span className="part-description">{part.partDescription}</span>
                                                                </div>
                                                                <span className="part-count">{part.replacementCount}x</span>
                                                            </div>
                                                        ))}
                                                    </div>
                                                )}
                                            </div>
                                        ) : (
                                            <p className="no-data">No parts data available for this customer in the selected filters</p>
                                        )}
                                    </div>
                                </div>
                                <div className="analysis-card">
                                    <div className="card-header">
                                        <FiSettings className="card-icon" />
                                        <div>
                                            <h4>Common Machine Types</h4>
                                            <p>Machine distribution for this customer</p>
                                        </div>
                                    </div>
                                    <div className="card-content">
                                        {customerMachines && customerMachines.length > 0 ? (
                                            <div className="machine-distribution">
                                                {customerMachines.slice(0, 5).map((machine: any, index: number) => (
                                                    <div key={index} className="machine-item">
                                                        <div className="machine-info">
                                                            <span className="machine-name">{machine.name}</span>
                                                            <span className="machine-percentage">{machine.percentage}%</span>
                                                        </div>
                                                        <div className="machine-bar">
                                                            <div
                                                                className="machine-fill"
                                                                style={{
                                                                    width: `${machine.percentage}%`,
                                                                    backgroundColor: machine.color || '#FF6B35'
                                                                }}
                                                            />
                                                        </div>
                                                    </div>
                                                ))}
                                            </div>
                                        ) : (
                                            <p className="no-data">No machine type data available for this customer in the selected filters</p>
                                        )}
                                    </div>
                                </div>

                                <div className="analysis-card">
                                    <div className="card-header">
                                        <FiUser className="card-icon" />
                                        <div>
                                            <h4>Top 3 Technicians</h4>
                                            <p>Most active technicians for this customer</p>
                                        </div>
                                    </div>
                                    <div className="card-content">
                                        {topTechnicians && topTechnicians.length > 0 ? (
                                            <div className="technicians-list">
                                                {topTechnicians.map((technician, index) => (
                                                    <div key={index} className="technician-item">
                                                        <div className="technician-rank">
                                                            <span className="rank-number">#{index + 1}</span>
                                                        </div>
                                                        <div className="technician-avatar">
                                                            {technician.name.charAt(0).toUpperCase()}
                                                        </div>
                                                        <div className="technician-details">
                                                            <span className="technician-name">{technician.name}</span>
                                                            <div className="technician-stats">
                                                                <span className="technician-count">{technician.count} SRs</span>
                                                                {technician.avg_resolution_days > 0 && (
                                                                    <span className="technician-resolution">
                                                                        Avg: {technician.avg_resolution_days} days
                                                                    </span>
                                                                )}
                                                            </div>
                                                        </div>
                                                    </div>
                                                ))}
                                            </div>
                                        ) : (
                                            <div className="no-data-info">
                                                <p>No technician data available for {selectedCustomer} in the selected filters</p>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            )}

            <style jsx>{`
                .filter-status-bar {
                    background-color: #e3f2fd;
                    color: #1976d2;
                    padding: 8px 16px;
                    margin-bottom: 20px;
                    border-left: 4px solid #1976d2;
                    font-size: 14px;
                    font-weight: 500;
                    display: flex;
                    align-items: center;
                    gap: 8px;
                }
                
                .filter-info {
                    display: flex;
                    align-items: center;
                    gap: 8px;
                }
                
                .filter-icon {
                    flex-shrink: 0;
                }
            `}</style>
        </div>
    );
};

export default CustomerAnalytics;



