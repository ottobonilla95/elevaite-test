import React, { useState, useEffect, useMemo } from 'react';
import {
    ResponsiveContainer, BarChart, Bar, XAxis, YAxis,
    Tooltip, Cell
} from 'recharts';
import _ from 'lodash';
import axios from 'axios';

// Define TypeScript interfaces
interface DateRange {
    fromDate: string;
    toDate: string;
}

interface RootCauseProps {
    dateRange: DateRange | null;
}

interface ProblemData {
    'Problem': string;  // Changed based on API response
    'Root cause': string;
    'Symptoms': string;
    'AI Usage ID': string;
    'Chat Duration': string;
}

interface SubCategory {
    name: string;
    percentage: string;
    count: number;
}

interface DetailedIssue {
    category: string;
    total: number;
    aiUsedCount: number;
    ElevAIte: string;
    aht: string;
    subCategories: SubCategory[];
}

interface ChartDataItem {
    name: string;
    value: number;
}

interface ProcessedData {
    detailedIssues: DetailedIssue[];
    chartData: ChartDataItem[];
    topCategories: string[];
}

// Define colors and gradients
const COLORS = ['#7C3AED', '#3B82F6', '#10B981', '#F59E0B', '#EF4444'];

// Pagination controls component
const PaginationControls: React.FC<{
    currentPage: number;
    totalPages: number;
    onPageChange: (page: number) => void;
}> = ({ currentPage, totalPages, onPageChange }) => {
    return (
        <div className="flex items-center justify-center mt-6 space-x-2">
            <button
                onClick={() => onPageChange(currentPage - 1)}
                disabled={currentPage === 1}
                className={`px-3 py-1 rounded-md ${currentPage === 1
                    ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                    : 'bg-slate-700 text-white hover:bg-slate-800'
                    }`}
            >
                Previous
            </button>

            <div className="flex items-center space-x-1">
                {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                    // Logic to show pages around current page
                    let pageToShow;
                    if (totalPages <= 5) {
                        pageToShow = i + 1;
                    } else if (currentPage <= 3) {
                        pageToShow = i + 1;
                    } else if (currentPage >= totalPages - 2) {
                        pageToShow = totalPages - 4 + i;
                    } else {
                        pageToShow = currentPage - 2 + i;
                    }

                    return (
                        <button
                            key={pageToShow}
                            onClick={() => onPageChange(pageToShow)}
                            className={`w-8 h-8 flex items-center justify-center rounded-md ${currentPage === pageToShow
                                ? 'bg-blue-600 text-white font-medium'
                                : 'bg-gray-200 text-slate-700 hover:bg-gray-300'
                                }`}
                        >
                            {pageToShow}
                        </button>
                    );
                })}

                {totalPages > 5 && currentPage < totalPages - 2 && (
                    <>
                        <span className="px-1">...</span>
                        <button
                            onClick={() => onPageChange(totalPages)}
                            className="w-8 h-8 flex items-center justify-center rounded-md bg-gray-200 text-slate-700 hover:bg-gray-300"
                        >
                            {totalPages}
                        </button>
                    </>
                )}
            </div>

            <button
                onClick={() => onPageChange(currentPage + 1)}
                disabled={currentPage === totalPages}
                className={`px-3 py-1 rounded-md ${currentPage === totalPages
                    ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                    : 'bg-slate-700 text-white hover:bg-slate-800'
                    }`}
            >
                Next
            </button>
        </div>
    );
};

// Custom card component
const CustomCard: React.FC<{
    children: React.ReactNode;
    gradientIndex?: number;
}> = ({ children, gradientIndex = 0 }) => {
    const gradients = [
        'from-indigo-500 to-purple-600',
        'from-blue-600 to-blue-500',
        'from-emerald-600 to-emerald-500'
    ];

    return (
        <div className="bg-white rounded-2xl shadow-lg hover:shadow-xl transition-all duration-300 hover:-translate-y-1 h-full relative overflow-hidden">
            <div className={`absolute top-0 left-0 right-0 h-1 bg-gradient-to-r ${gradients[gradientIndex]}`}></div>
            {children}
        </div>
    );
};

// Custom tooltip for bar chart
const CustomTooltip: React.FC<any> = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
        return (
            <div className="bg-white p-3 border border-gray-200 rounded shadow-md">
                <p className="font-medium">{label}</p>
                <p className="text-blue-600">{`${payload[0].value} cases`}</p>
            </div>
        );
    }
    return null;
};

const RootCause: React.FC<RootCauseProps> = ({ dateRange }) => {
    const [loading, setLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);
    const [data, setData] = useState<ProblemData[]>([]);

    // Pagination state
    const [currentPage, setCurrentPage] = useState<number>(1);
    const [itemsPerPage, setItemsPerPage] = useState<number>(5);

    useEffect(() => {
        const fetchData = async () => {
            setLoading(true);

            try {
                // For debugging - check what dates we're getting
                console.log("Root Cause Tab - date range received:", dateRange);

                // Always set up params, even if dateRange is null
                let params: any = {};

                // Add date parameters if we have them
                if (dateRange && dateRange.fromDate && dateRange.toDate) {
                    params = {
                        from: dateRange.fromDate,
                        to: dateRange.toDate
                    };
                    console.log("Root Cause Tab - using date params:", params);
                } else {
                    console.log("Root Cause Tab - using no date params");
                }

                // Use the problems-data endpoint since it's working for other tabs
                const response = await axios.get(`http://localhost:5000/api/problems-data`, { params });
                console.log("Root Cause Tab - API response received:", response.data?.length || 'no data');

                if (response.data && Array.isArray(response.data)) {
                    setData(response.data);
                } else {
                    console.error("Root Cause Tab - invalid response format:", response.data);
                    setData([]);
                }
            } catch (error) {
                console.error('Root Cause Tab - Error fetching data:', error);
                setError(error instanceof Error ? error.message : 'An unknown error occurred');
                setData([]);
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, [dateRange]);

    const processedData = useMemo<ProcessedData | null>(() => {
        if (!data || !data.length) {
            console.log("Root Cause Tab - No data to process");
            return null;
        }

        console.log("Root Cause Tab - Processing data:", data.length, "records");
        console.log("Root Cause Tab - Sample record:", data[0]);

        // First, filter out Case Closed and Duplicate Case
        const filteredData = data.filter(item => {
            // Safely check if 'Root cause' exists and is a string before calling toLowerCase()
            const rootCause = item['Root cause'];
            if (!rootCause || typeof rootCause !== 'string') {
                console.log("Root Cause Tab - Filtering out null root cause:", item);
                return false;
            }

            const lowerRootCause = rootCause.toLowerCase().trim();
            return !lowerRootCause.includes('case closed') && !lowerRootCause.includes('duplicate case');
        });

        console.log("Root Cause Tab - Filtered data count:", filteredData.length);

        const rootCauseCounts = _.groupBy(filteredData, 'Root cause');
        console.log("Root Cause Tab - Root cause groups:", Object.keys(rootCauseCounts).length);

        const cleanRootCause = (cause: string) => {
            if (!cause) return 'Unknown';
            try {
                return cause.split('(')[0].trim();
            } catch (e) {
                return cause;
            }
        };

        const detailedIssues: DetailedIssue[] = Object.entries(rootCauseCounts)
            .map(([category, items]) => {
                const itemsArray = items as ProblemData[];
                const validCategory = category || 'Unknown';

                // For debugging
                console.log(`Root Cause Tab - Processing category: ${validCategory} with ${itemsArray.length} items`);

                try {
                    return {
                        category: cleanRootCause(validCategory),
                        total: itemsArray.length,
                        aiUsedCount: itemsArray.filter(item => item['AI Usage ID'] === 'Yes').length,
                        ElevAIte: ((itemsArray.filter(item => item['AI Usage ID'] === 'Yes').length / itemsArray.length) * 100).toFixed(0),
                        aht: itemsArray.some(item => item['Chat Duration'] && !isNaN(parseFloat(item['Chat Duration']))) ?
                            (_.meanBy(itemsArray.filter(item => item['Chat Duration'] && !isNaN(parseFloat(item['Chat Duration']))),
                                item => {
                                    try {
                                        // Handle duration in format "MM:SS"
                                        if (typeof item['Chat Duration'] === 'string' && item['Chat Duration'].includes(':')) {
                                            const [minutes, seconds] = item['Chat Duration'].split(':').map(Number);
                                            return minutes + (seconds / 60);
                                        }
                                        return parseFloat(item['Chat Duration']);
                                    } catch (e) {
                                        console.error("Error parsing Chat Duration:", e);
                                        return 0;
                                    }
                                }) || 0).toFixed(2) : 'N/A',
                        subCategories: Object.entries(_.groupBy(itemsArray, 'Symptoms'))
                            .map(([name, subItems]) => {
                                const typedSubItems = subItems as ProblemData[];
                                const validName = name || 'Unknown';
                                return {
                                    name: validName,
                                    percentage: ((typedSubItems.length / itemsArray.length) * 100).toFixed(0),
                                    count: typedSubItems.length
                                };
                            })
                            .sort((a, b) => b.count - a.count)
                            .slice(0, 3)
                    };
                } catch (e) {
                    console.error("Error processing category:", validCategory, e);
                    return {
                        category: validCategory,
                        total: itemsArray.length,
                        aiUsedCount: 0,
                        ElevAIte: "0",
                        aht: "N/A",
                        subCategories: []
                    };
                }
            })
            .sort((a, b) => b.total - a.total);

        console.log("Root Cause Tab - Processed detailed issues:", detailedIssues.length);

        const chartData = detailedIssues
            .slice(0, 3)
            .map(issue => ({
                name: issue.category,
                value: issue.total
            }));

        return {
            detailedIssues,
            chartData,
            topCategories: detailedIssues.slice(0, 5).map(issue => issue.category)
        };
    }, [data]);

    // Calculate pagination
    const paginatedData = useMemo(() => {
        if (!processedData) {
            console.log("Root Cause Tab - No processed data for pagination");
            return { top3Issues: [], paginatedIssues: [], totalPages: 0 };
        }

        console.log("Root Cause Tab - Calculating pagination");

        // Get top 3 issues separately for cards
        const top3Issues = processedData.detailedIssues.slice(0, 3);

        // Get remaining issues for paginated table
        const remainingIssues = processedData.detailedIssues.slice(3);

        // Calculate total pages
        const totalPages = Math.max(1, Math.ceil(remainingIssues.length / itemsPerPage));

        // Get current page issues
        const startIndex = (currentPage - 1) * itemsPerPage;
        const paginatedIssues = remainingIssues.slice(startIndex, startIndex + itemsPerPage);

        console.log(`Root Cause Tab - Pagination: ${paginatedIssues.length} items on page ${currentPage} of ${totalPages}`);

        return {
            top3Issues,
            paginatedIssues,
            totalPages
        };
    }, [processedData, currentPage, itemsPerPage]);

    const handlePageChange = (page: number) => {
        setCurrentPage(page);
    };

    if (loading) return (
        <div className="flex justify-center items-center h-64 bg-gray-50">
            <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
        </div>
    );

    if (error) return (
        <div className="flex justify-center items-center h-64 bg-gray-50 text-red-500">
            Error: {error}
        </div>
    );

    if (!processedData || (!processedData.detailedIssues || processedData.detailedIssues.length === 0)) {
        return (
            <div className="flex justify-center items-center h-64 bg-gray-50">
                <p className="text-gray-500">No root cause data available for the selected date range.</p>
            </div>
        );
    }

    const { chartData } = processedData;
    const { top3Issues, paginatedIssues, totalPages } = paginatedData;

    return (
        <div className="p-8 bg-gray-50 min-h-screen overflow-y-auto">
            {/* Header */}
            <h1 className="mb-8 text-3xl font-semibold bg-gradient-to-r from-slate-800 to-slate-600 bg-clip-text text-transparent">
                Root Cause Analysis
            </h1>

            {/* Top 3 Root Causes */}
            {top3Issues.length > 0 && (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-10">
                    {top3Issues.map((issue, index) => (
                        <div key={`top-${issue.category}-${index}`} className="transition-opacity duration-500 opacity-100">
                            <CustomCard gradientIndex={index}>
                                <div className="p-6">
                                    <h2 className="text-xl font-semibold text-slate-800 mb-4">{issue.category}</h2>

                                    <div className="grid grid-cols-2 gap-4 mb-6">
                                        <div className="text-center">
                                            <p className="text-3xl font-bold" style={{ color: COLORS[index] }}>
                                                {issue.total}
                                            </p>
                                            <p className="text-sm text-slate-500 mt-1">
                                                Total Cases
                                            </p>
                                        </div>
                                        <div className="text-center">
                                            <p className="text-3xl font-bold" style={{ color: COLORS[index] }}>
                                                {issue.ElevAIte}%
                                            </p>
                                            <p className="text-sm text-slate-500 mt-1">
                                                ElevAIte Usage Rate
                                            </p>
                                        </div>
                                    </div>

                                    <div className="bg-slate-50 p-4 rounded-lg mb-6">
                                        <div className="flex items-center gap-2 text-slate-700">
                                            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                                                <path fillRule="evenodd" d="M12 7a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0V8.414l-4.293 4.293a1 1 0 01-1.414 0L8 10.414l-4.293 4.293a1 1 0 01-1.414-1.414l5-5a1 1 0 011.414 0L11 10.586 14.586 7H12z" clipRule="evenodd" />
                                            </svg>
                                            <h3 className="font-semibold">AHT: {issue.aht} min</h3>
                                        </div>
                                    </div>

                                    <div className="border-t border-gray-200 pt-4">
                                        <h3 className="text-slate-700 font-semibold mb-3">
                                            Top Symptoms
                                        </h3>

                                        {issue.subCategories.map((sub, subIndex) => (
                                            <div key={`sub-${sub.name}-${subIndex}`} className="mb-3">
                                                <div className="flex justify-between mb-1">
                                                    <p className="text-sm text-slate-500">{sub.name}</p>
                                                    <p className="text-sm font-medium text-slate-500">
                                                        {sub.count} ({sub.percentage}%)
                                                    </p>
                                                </div>
                                                <div className="w-full bg-gray-200 rounded-full h-2">
                                                    <div
                                                        className="h-2 rounded-full"
                                                        style={{
                                                            width: `${sub.percentage}%`,
                                                            backgroundColor: COLORS[index]
                                                        }}
                                                    ></div>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            </CustomCard>
                        </div>
                    ))}
                </div>
            )}

            {/* Bar Chart */}
            {chartData && chartData.length > 0 && (
                <div className="bg-white rounded-2xl shadow-lg overflow-hidden mb-10 transition-opacity duration-500 opacity-100">
                    <div className="bg-gradient-to-r from-slate-800 to-slate-600 text-white p-4">
                        <h2 className="text-xl font-semibold">Trend Analysis</h2>
                    </div>
                    <div className="p-6">
                        <div className="h-96 w-full">
                            <ResponsiveContainer width="100%" height="100%">
                                <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 70 }}>
                                    <XAxis
                                        dataKey="name"
                                        tick={{
                                            fill: '#1e293b',
                                            fontSize: 12,
                                            width: 200,
                                            textAnchor: 'middle',
                                            dy: 10,
                                            dx: -10
                                        }}
                                        height={120}
                                        label={{
                                            value: 'Root Causes',
                                            position: 'bottom',
                                            offset: 0,
                                            fill: '#1e293b',
                                            fontSize: 14
                                        }}
                                        interval={0}
                                    />
                                    <YAxis
                                        tick={{ fill: '#1e293b' }}
                                        label={{
                                            value: 'Number of Cases',
                                            angle: -90,
                                            position: 'left',
                                            offset: 0,
                                            fill: '#1e293b',
                                            fontSize: 14
                                        }}
                                    />
                                    <Tooltip content={<CustomTooltip />} />
                                    <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                                        {chartData.map((entry, index) => (
                                            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                        ))}
                                    </Bar>
                                </BarChart>
                            </ResponsiveContainer>
                        </div>
                    </div>
                </div>
            )}

            {/* Items Per Page Dropdown */}
            {paginatedIssues.length > 0 && (
                <div className="flex items-center justify-between mb-4">
                    <h2 className="text-xl font-semibold text-slate-800">Additional Root Causes</h2>
                    <div className="flex items-center space-x-2">
                        <label htmlFor="itemsPerPage" className="text-sm text-slate-600">Items per page:</label>
                        <select
                            id="itemsPerPage"
                            value={itemsPerPage}
                            onChange={(e) => {
                                setItemsPerPage(Number(e.target.value));
                                setCurrentPage(1); // Reset to first page when changing items per page
                            }}
                            className="border border-gray-300 rounded px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                        >
                            <option value={5}>5</option>
                            <option value={10}>10</option>
                            <option value={15}>15</option>
                            <option value={20}>20</option>
                        </select>
                    </div>
                </div>
            )}

            {/* Table View */}
            {paginatedIssues.length > 0 && (
                <div className="bg-white rounded-2xl shadow-lg overflow-hidden mb-4">
                    <div className="overflow-x-auto">
                        <table className="min-w-full divide-y divide-gray-200">
                            <thead>
                                <tr className="bg-gradient-to-r from-blue-700 to-indigo-900">
                                    <th className="px-6 py-3 text-left text-xs font-medium text-white uppercase tracking-wider">Root Cause</th>
                                    <th className="px-6 py-3 text-right text-xs font-medium text-white uppercase tracking-wider">Total Cases</th>
                                    <th className="px-6 py-3 text-right text-xs font-medium text-white uppercase tracking-wider">ElevAIte Usage Rate</th>
                                    <th className="px-6 py-3 text-right text-xs font-medium text-white uppercase tracking-wider">AHT (min)</th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-white uppercase tracking-wider">Top Symptoms</th>
                                </tr>
                            </thead>
                            <tbody className="bg-white divide-y divide-gray-200">
                                {paginatedIssues.map((issue, index) => (
                                    <tr key={`row-${issue.category}-${index}`} className="hover:bg-gray-50 transition-colors">
                                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-slate-700">{issue.category}</td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-right font-medium text-slate-700">{issue.total}</td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-slate-700">{issue.ElevAIte}%</td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-slate-700">{issue.aht}</td>
                                        <td className="px-6 py-4 text-sm text-slate-500">
                                            {issue.subCategories.map((sub, idx) =>
                                                `${sub.name} (${sub.count})${idx < issue.subCategories.length - 1 ? ', ' : ''}`
                                            )}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}

            {/* Pagination Controls */}
            {totalPages > 1 && (
                <PaginationControls
                    currentPage={currentPage}
                    totalPages={totalPages}
                    onPageChange={handlePageChange}
                />
            )}

            {/* Empty State */}
            {top3Issues.length === 0 && paginatedIssues.length === 0 && (
                <div className="text-center py-6 bg-white rounded-lg shadow">
                    <p className="text-slate-600">No root causes found for the selected date range.</p>
                </div>
            )}
        </div>
    );
};

export default RootCause;