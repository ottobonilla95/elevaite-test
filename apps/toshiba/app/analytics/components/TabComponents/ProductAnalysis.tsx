"use client";

import React, { useEffect, useState } from 'react';
import { FiDownload, FiBarChart, FiPieChart, FiClock, FiPackage, FiTool, FiAlertCircle, FiTrendingUp, FiTarget, FiFilter } from "react-icons/fi";

import './ProductAnalysis.scss';

import CustomBarChart from '../SubComponents/BarChart';
import CustomPieChart from '../SubComponents/PieChart';
import MachineDetailPanel from '../SubComponents/MachineDetailPanel';
import TopModelsByMachineType from '../SubComponents/TopModelsByMachineType';
import Table, { Column } from '../SubComponents/Table';

import { DateFilters } from '../Tabs';
import {
    fetchMachineOverview,
    fetchMachineDetails,
    fetchPartsAnalysis,
    fetchPartsByMachineType,
    fetchPartsByMachineFiltered,
    fetchMachineFieldDistribution,
    fetchMachineTypeFieldSummary
} from '../../lib/actions';
import type {
    MachineOverviewData,
    MachineDetail,
    PartsData
} from '../../lib/types';

export interface ReplacementPart {
    partNumber: string;
    description: string;
    count: number;
    machineType?: string;
}

interface MachinePartsBreakdown {
    machineType: string;
    serviceRequests: number;
    totalPartsOrdered: number;
    uniquePartsCount: number;
    topParts: Array<{
        partNumber: string;
        description: string;
        count: number;
    }>;
}

// NEW INTERFACES FOR FIELD DISTRIBUTION
interface MachineFieldData {
    machineType: string;
    machineModel: string;
    totalSRs: number;
    machinesInField: number;
    srRate: number;
    uniqueMachinesWithSRs: number;
}

interface MachineTypeSummary {
    machineType: string;
    totalMachinesInField: number;
    totalSRs: number;
    uniqueMachinesWithSRs: number;
    srRate: number;
}

interface FieldDistributionResponse {
    fieldDistribution: MachineFieldData[];
    summary: {
        totalMachineTypesModels: number;
        avgSRRate: number;
        totalFieldPopulation: number;
        dateRange: {
            startDate: string | null;
            endDate: string | null;
        };
    };
}

// Add FST Filter interfaces
interface ManagerFilter {
    managerId: number | null;
    managerName: string;
}

interface FSTFilter {
    fstId: number | null;
    fstName: string;
}

interface ProductAnalysisProps {
    dateFilters: DateFilters;
    managerFilter?: ManagerFilter;
    fstFilter?: FSTFilter;
}

const ProductAnalysis: React.FC<ProductAnalysisProps> = ({
    dateFilters,
    managerFilter,
    fstFilter
}) => {
    const [loading, setLoading] = useState(true);
    const [machineOverview, setMachineOverview] = useState<MachineOverviewData | null>(null);
    const [machineDetails, setMachineDetails] = useState<MachineDetail[]>([]);
    const [partsData, setPartsData] = useState<PartsData[]>([]);
    const [filteredPartsData, setFilteredPartsData] = useState<PartsData[]>([]);
    const [machinePartsBreakdown, setMachinePartsBreakdown] = useState<MachinePartsBreakdown[]>([]);


    const [fieldData, setFieldData] = useState<FieldDistributionResponse | null>(null);
    const [typeSummary, setTypeSummary] = useState<MachineTypeSummary[]>([]);

    const [selectedMachine, setSelectedMachine] = useState<string>('all');
    const [loadingFiltered, setLoadingFiltered] = useState(false);

    const [dateError, setDateError] = useState<string>('');

    const [productType, setProductType] = useState<'all' | 'toshiba'>('all'); const validateDateRange = (startDate: string, endDate: string): string => {
        if (!startDate && !endDate) return '';

        if (startDate && endDate) {
            const start = new Date(startDate);
            const end = new Date(endDate);
            const now = new Date();

            if (start > end) {
                return 'Start date cannot be after end date';
            }
            if (start > now || end > now) {
                return 'Dates cannot be in the future';
            }

            const diffTime = Math.abs(end.getTime() - start.getTime());
            const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
            if (diffDays > 730) {
                return 'Date range cannot exceed 2 years';
            }
        }

        return '';
    };


    useEffect(() => {
        const error = validateDateRange(dateFilters.startDate, dateFilters.endDate);
        setDateError(error);

        if (!error) {
            loadData();
        }
    }, [dateFilters, managerFilter, fstFilter, productType]); // Added productType

    useEffect(() => {
        if (selectedMachine && selectedMachine !== 'all' && partsData.length > 0) {
            loadFilteredParts();
        } else if (selectedMachine === 'all') {
            setFilteredPartsData(partsData);
        }
    }, [selectedMachine, partsData]);

    const fetchFieldDistribution = async (filters: any) => {
        try {
            console.log('Fetching field distribution data with filters:', filters);

            const [fieldResult, summaryResult] = await Promise.allSettled([
                fetchMachineFieldDistribution(filters),
                fetchMachineTypeFieldSummary(filters)
            ]);

            if (fieldResult.status === 'fulfilled') {
                console.log('Field distribution result:', fieldResult.value);
                setFieldData(fieldResult.value);
            } else {
                console.error('Field distribution error:', fieldResult.reason);
            }

            if (summaryResult.status === 'fulfilled') {
                console.log('Summary result:', summaryResult.value);
                setTypeSummary(summaryResult.value);
            } else {
                console.error('Summary error:', summaryResult.reason);
            }
        } catch (error) {
            console.error('Error fetching field distribution:', error);
        }
    };

    const loadData = async () => {
        try {
            setLoading(true);


            const filters = {
                start_date: dateFilters.startDate,
                end_date: dateFilters.endDate,
                manager_id: managerFilter?.managerId,
                fst_id: fstFilter?.fstId,
                product_type: productType

            };

            console.log('ProductAnalysis - Loading data with filters:', filters);

            const [overview, details, parts, partsByMachine] = await Promise.allSettled([
                fetchMachineOverview(filters),
                fetchMachineDetails(filters),
                fetchPartsAnalysis(filters, 100),
                fetchPartsByMachineType(filters)
            ]);


            await fetchFieldDistribution(filters);

            if (overview.status === 'fulfilled') {
                console.log("🌐 Machine Overview Response:", overview.value);
                console.log("🌐 topModelsByType specifically:", overview.value?.topModelsByType);
                setMachineOverview(overview.value);
            } else {
                console.error("Error fetching machine overview:", overview.reason);
            }

            if (details.status === 'fulfilled') {
                setMachineDetails(details.value || []);
            } else {
                console.error("Error fetching machine details:", details.reason);
                setMachineDetails([]);
            }

            if (parts.status === 'fulfilled') {
                const partsArray = Array.isArray(parts.value) ? parts.value : [];
                setPartsData(partsArray);
                setFilteredPartsData(partsArray);
            } else {
                console.error("Error fetching parts data:", parts.reason);
                setPartsData([]);
                setFilteredPartsData([]);
            }

            if (partsByMachine.status === 'fulfilled') {
                setMachinePartsBreakdown(partsByMachine.value || []);
            } else {
                console.error("Error fetching parts by machine type:", partsByMachine.reason);
                setMachinePartsBreakdown([]);
            }

        } catch (error) {
            console.error("Error loading product data:", error);
        } finally {
            setLoading(false);
        }
    };

    const loadFilteredParts = async () => {
        try {
            setLoadingFiltered(true);
            console.log('Loading filtered parts for machine:', selectedMachine);


            const filters = {
                start_date: dateFilters.startDate,
                end_date: dateFilters.endDate,
                machine_type: selectedMachine,
                manager_id: managerFilter?.managerId,
                fst_id: fstFilter?.fstId,
                product_type: productType

            };

            const filtered = await fetchPartsByMachineFiltered(filters);
            console.log('Filtered parts response:', filtered);

            if (Array.isArray(filtered) && filtered.length > 0) {
                setFilteredPartsData(filtered);
            } else {
                console.log('No parts found for machine type:', selectedMachine);
                setFilteredPartsData([]);
            }
        } catch (error) {
            console.error("Error loading filtered parts:", error);
            setFilteredPartsData([]);
        } finally {
            setLoadingFiltered(false);
        }
    };

    const getMachineTypesForDropdown = () => {
        const types = ['all'];
        if (machineOverview?.typeDistribution) {
            types.push(...machineOverview.typeDistribution.map(item => item.name));
        }
        if (machinePartsBreakdown) {
            const additionalTypes = machinePartsBreakdown.map(item => item.machineType);
            additionalTypes.forEach(type => {
                if (!types.includes(type)) {
                    types.push(type);
                }
            });
        }
        return types;
    };

    if (dateError) {
        return (
            <div className='summary-container'>
                <div className="date-error-banner">
                    <FiAlertCircle className="error-icon" />
                    <div>
                        <h3>Invalid Date Range</h3>
                        <p>{dateError}</p>
                        <small>Please adjust your date filters and try again.</small>
                    </div>
                </div>
            </div>
        );
    }

    if (loading) {
        return (
            <div className='summary-container'>
                <div className="loading-state">
                    <div className="loading-spinner"></div>
                    <p>Loading product analytics...</p>
                </div>
            </div>
        );
    }

    if (!machineOverview) {
        return (
            <div className='summary-container'>
                <div className="no-data-state">
                    <FiTool size={48} color="#ccc" />
                    <p>No machine data available</p>
                </div>
            </div>
        );
    }

    const replacementParts: ReplacementPart[] = filteredPartsData.map(part => ({
        partNumber: part.partNumber || 'N/A',
        description: part.description || 'No description available',
        count: typeof part.count === 'number' ? part.count : parseInt(part.count) || 0,
        machineType: part.machineType || undefined
    }));

    const columns: Column<ReplacementPart>[] = [
        {
            label: "Part Number",
            key: "partNumber",
            render: (value) => <span className="part-number">{value}</span>
        },
        {
            label: "Description",
            key: "description",
            render: (value) => (
                <div style={{
                    whiteSpace: 'normal',
                    maxWidth: '400px',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis'
                }}>
                    {value}
                </div>
            )
        },
        {
            label: "Count",
            key: "count",
            render: (value) => <span className="tag">{value}</span>
        }
    ];


    const fieldColumns: Column<MachineTypeSummary>[] = [
        {
            label: "Machine Type",
            key: "machineType",
            render: (value) => <span className="machine-type">{value}</span>
        },
        {
            label: "Total in Field",
            key: "totalMachinesInField",
            render: (value) => <span className="field-count">{value.toLocaleString()}</span>
        },
        {
            label: "Total SRs",
            key: "totalSRs",
            render: (value) => <span className="sr-count">{value.toLocaleString()}</span>
        },
        {
            label: "SR Rate",
            key: "srRate",
            render: (value) => <span className="sr-rate">{value.toFixed(2)} per machine</span>
        },
        {
            label: "Machines with SRs",
            key: "uniqueMachinesWithSRs",
            render: (value) => <span className="machines-with-srs">{value.toLocaleString()}</span>
        }
    ];

    const pieChartData = machineOverview?.typeDistribution?.slice(0, 5).map((item, index) => ({
        name: item.name,
        value: item.value,
        count: item.count,
        color: item.color || ["#FF681F", "#FF9F71", "#FFD971", "#BF0909", "#FFBD71", "#FF0000"][index] || "#CCCCCC"
    })) || [];

    return (
        <div className='summary-container'>
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

            <div className="product-type-tabs">
                <h3>Product Category</h3>
                <div className="tab-buttons">
                    <button
                        className={`tab-btn ${productType === 'all' ? 'active' : ''}`}
                        onClick={() => setProductType('all')}
                    >
                        All Products
                    </button>
                    <button
                        className={`tab-btn ${productType === 'toshiba' ? 'active' : ''}`}
                        onClick={() => setProductType('toshiba')}
                    >
                        TGCS Products
                    </button>
                </div>
                {productType === 'toshiba' && (
                    <p className="active-filter-info">
                        Showing TGCS machine types only
                    </p>
                )}
            </div>

            <div className='machine-summary-container'>
                <h2><b>Machine Overview</b></h2>

                <div className="charts-grid">
                    <div className="chart-box">
                        <h4>Total SRs by Machine Type</h4>
                        <CustomBarChart data={machineOverview.typeBarChart} />
                    </div>
                    <div className="chart-box">
                        <h4>Machine Types Distribution</h4>
                        <CustomPieChart data={pieChartData} />
                    </div>
                </div>

                <div className="top-models-section">
                    <h3>Top 5 Models per Machine Type</h3>
                    <TopModelsByMachineType data={machineOverview.topModelsByType || []} />
                </div>
            </div>

            {/* NEW FIELD DISTRIBUTION SECTION */}
            <div className='machine-summary-container'>
                <h2><b>Product Distribution Relative to Field Population</b></h2>
                <p>Service request rates per machine type based on total machines in field</p>

                {fieldData && (
                    <div className="field-summary-stats">
                        <div className="stat-card">
                            <FiTarget className="stat-icon" />
                            <div>
                                <div className="stat-value">{fieldData.summary.totalFieldPopulation.toLocaleString()}</div>
                                <div className="stat-label">Total Machines in Field</div>
                            </div>
                        </div>
                        <div className="stat-card">
                            <FiTrendingUp className="stat-icon" />
                            <div>
                                <div className="stat-value">{fieldData.summary.avgSRRate.toFixed(2)}</div>
                                <div className="stat-label">Avg SR Rate per Machine</div>
                            </div>
                        </div>
                        <div className="stat-card">
                            <FiBarChart className="stat-icon" />
                            <div>
                                <div className="stat-value">{typeSummary.length}</div>
                                <div className="stat-label">Machine Types Analyzed</div>
                            </div>
                        </div>
                    </div>
                )}

                {typeSummary.length > 0 && (
                    <div className="detailed-field-analysis">
                        <Table<MachineTypeSummary>
                            data={typeSummary}
                            columns={fieldColumns}
                            showPagination={true}
                            title="Machine Field Distribution Analysis"
                        />
                    </div>
                )}
            </div>

            <div className='machine-summary-container'>
                <h2><b>Parts Analysis by Machine Type</b></h2>
                <p>Parts ordered breakdown per machine type</p>

                {machinePartsBreakdown.length > 0 ? (
                    <div className="parts-breakdown-grid">
                        {machinePartsBreakdown.map((machine, index) => (
                            <div key={index} className="machine-parts-card">
                                <div className="card-header">
                                    <FiPackage className="card-icon" />
                                    <div>
                                        <h3>{machine.machineType}</h3>
                                        <p>{machine.serviceRequests} Service Requests</p>
                                    </div>
                                </div>

                                <div className="parts-metrics">
                                    <div className="metric-item">
                                        <span className="metric-label">Parts Ordered:</span>
                                        <span className="metric-value">{machine.totalPartsOrdered.toLocaleString()}</span>
                                    </div>
                                    <div className="metric-item">
                                        <span className="metric-label">Unique Parts:</span>
                                        <span className="metric-value">{machine.uniquePartsCount}</span>
                                    </div>
                                </div>

                                {machine.topParts.length > 0 && (
                                    <div className="top-parts-section">
                                        <h4>Top 5 Parts by Count for {machine.machineType}:</h4>
                                        <small className="sort-note">Sorted by replacement count (highest first)</small>
                                        {machine.topParts.map((part, partIndex) => (
                                            <div key={partIndex} className="part-item">
                                                <div className="part-info">
                                                    <span className="part-number">{part.partNumber}</span>
                                                    <span className="part-desc">{part.description}</span>
                                                </div>
                                                <div className="part-stats">
                                                    <span className="part-count">{part.count}×</span>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                ) : (
                    <div className="no-data-message">
                        <FiPackage size={48} color="#ccc" />
                        <p>No parts by machine type data available</p>
                    </div>
                )}
            </div>

            <div className='machine-summary-container'>
                <div className='table-header'>
                    <div>
                        <h2><b>Most Common Replacement Parts</b></h2>
                        <p>Filter by machine type or view all parts (sorted by count)</p>
                        {selectedMachine !== 'all' && (
                            <small>Showing {filteredPartsData.length} parts for {selectedMachine}</small>
                        )}
                    </div>
                    <div className="table-controls">
                        <select
                            value={selectedMachine}
                            onChange={(e) => setSelectedMachine(e.target.value)}
                            className="machine-filter-select"
                        >
                            <option value="all">All Machine Types</option>
                            {getMachineTypesForDropdown().slice(1).map((type, index) => (
                                <option key={index} value={type}>{type}</option>
                            ))}
                        </select>
                    </div>
                </div>

                {loadingFiltered ? (
                    <div className="loading-filtered">
                        <div className="loading-spinner"></div>
                        <p>Loading filtered parts...</p>
                    </div>
                ) : replacementParts && replacementParts.length > 0 ? (
                    <Table<ReplacementPart>
                        data={replacementParts}
                        columns={columns}
                        showPagination={true}
                        title={''}
                    />
                ) : (
                    <div className="no-parts-data">
                        <FiPackage size={48} color="#ccc" />
                        <p>No replacement parts data available for the selected machine type</p>
                        {selectedMachine !== 'all' && (
                            <button
                                onClick={() => setSelectedMachine('all')}
                                className="reset-filter-btn"
                            >
                                Show All Parts
                            </button>
                        )}
                    </div>
                )}
            </div>

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

export default ProductAnalysis;