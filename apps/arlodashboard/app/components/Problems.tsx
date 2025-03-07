import React, { useEffect, useMemo, useState } from 'react';
import { Bar, BarChart, ResponsiveContainer, XAxis, YAxis, Tooltip } from 'recharts';
import _ from 'lodash';
import axios from 'axios';

// Define TypeScript interfaces
interface DateRange {
    fromDate: string;
    toDate: string;
}

interface ProblemsProps {
    dateRange: DateRange | null;
}

interface ProblemData {
    Problem: string;
    'Root cause': string;
    Symptoms: string;
    'AI Usage ID': string;
    'Chat Duration': string;
}

interface Metrics {
    total: number;
    aiUsed: number;
    aiPercentage: string | number;
    topProblem: { name: string; count: number } | null;
    distributionData: { name: string; value: number }[];
}

// Custom tooltip component for the chart
const CustomTooltip: React.FC<any> = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
        return (
            <div className="bg-white p-3 border border-gray-200 rounded shadow-md">
                <p className="font-medium">{label}</p>
                <p className="text-blue-600">{`Cases: ${payload[0].value}`}</p>
            </div>
        );
    }
    return null;
};

const Problems: React.FC<ProblemsProps> = ({ dateRange }) => {
    const [data, setData] = useState<ProblemData[]>([]);
    const [problems, setProblems] = useState<string[]>([]);
    const [selectedProblem, setSelectedProblem] = useState<string>("all_problems");
    const [rootCauses, setRootCauses] = useState<string[]>([]);
    const [filteredData, setFilteredData] = useState<ProblemData[]>([]);
    const [selectedRootCause, setSelectedRootCause] = useState<string>("all_causes");
    const [symptoms, setSymptoms] = useState<string[]>([]);
    const [selectedSymptom, setSelectedSymptom] = useState<string>("all_symptoms");
    const [page, setPage] = useState<number>(0);
    const [rowsPerPage, setRowsPerPage] = useState<number>(10);
    const [loading, setLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);
    const [staticData, setStaticData] = useState<ProblemData[]>([]);

    // Items to filter out
    const excludedItems = ["Offline", "Disconnected Phone", "disconnected phone"];

    useEffect(() => {
        const fetchData = async () => {
            if (!dateRange) {
                return; // Don't make the API call if dateRange is not available
            }

            try {
                setLoading(true);
                const response = await axios.get(`http://localhost:5000/api/problems-data`, {
                    params: {
                        from: dateRange.fromDate,
                        to: dateRange.toDate
                    }
                });
                const responseData = response.data as ProblemData[];
                console.log("responsedata", responseData);

                if (responseData && responseData.length > 0) {
                    // Filter out excluded items and empty entries from the initial data
                    const filteredResponseData = responseData.filter(row =>
                        row &&
                        !excludedItems.includes(row.Problem) &&
                        !excludedItems.includes(row['Root cause']) &&
                        // Ensure the row has at least one of these fields populated
                        ((row.Problem && row.Problem.trim() !== '') ||
                            (row['Root cause'] && row['Root cause'].trim() !== '') ||
                            (row.Symptoms && row.Symptoms.trim() !== ''))
                    );

                    const uniqueProblems = _.uniq(filteredResponseData.map(row => row.Problem))
                        .filter(problem => problem !== "" && problem !== null && problem !== undefined && problem !== 0)
                        .sort();
                    const uniqueSymptoms = _.uniq(filteredResponseData.map(row => row.Symptoms))
                        .filter(symptom => symptom !== "" && symptom !== null && symptom !== undefined && symptom !== 0)
                        .sort();

                    setProblems(uniqueProblems);
                    setSymptoms(uniqueSymptoms);
                    setData(filteredResponseData);
                    setFilteredData(filteredResponseData);
                    setStaticData(filteredResponseData);
                }
                setLoading(false);
            } catch (error) {
                console.error('Error fetching data:', error);
                setError(error instanceof Error ? error.message : 'An unknown error occurred');
                setLoading(false);
            }
        };
        fetchData();
    }, [dateRange]);

    useEffect(() => {
        // Start with full dataset
        let filteredResults = [...data];

        // Filter out empty and invalid rows first
        filteredResults = filteredResults.filter(row =>
            // Remove rows that have no valid problem, root cause or symptoms
            row &&
            // Ensure the row has at least one of these fields populated
            ((row.Problem && row.Problem.trim() !== '') ||
                (row['Root cause'] && row['Root cause'].trim() !== '') ||
                (row.Symptoms && row.Symptoms.trim() !== ''))
        );

        // Apply problem filter
        if (selectedProblem !== "all_problems") {
            filteredResults = filteredResults.filter(row => row.Problem === selectedProblem);
        }

        // Apply root cause filter
        if (selectedRootCause !== "all_causes") {
            filteredResults = filteredResults.filter(row => row['Root cause'] === selectedRootCause);
        }

        // Apply symptom filter
        if (selectedSymptom !== "all_symptoms") {
            filteredResults = filteredResults.filter(row => row.Symptoms === selectedSymptom);
        }

        // Additional filter to ensure excluded items don't appear
        filteredResults = filteredResults.filter(row =>
            !excludedItems.includes(row.Problem) &&
            !excludedItems.includes(row['Root cause'])
        );

        // Update filtered data
        setFilteredData(filteredResults);

        // Update UI filter options based on selected filters
        if (selectedProblem !== "all_problems") {
            const uniqueRootCauses = _.uniq(filteredResults.map(row => row['Root cause']))
                .filter(cause =>
                    cause !== "" &&
                    cause !== null &&
                    cause !== undefined &&
                    !excludedItems.includes(cause)
                )
                .sort();
            setRootCauses(uniqueRootCauses);
        } else {
            setRootCauses([]);
        }

        if (selectedProblem !== "all_problems" || selectedRootCause !== "all_causes") {
            const uniqueSymptoms = _.uniq(filteredResults.map(row => row.Symptoms))
                .filter(symptom =>
                    symptom !== "" &&
                    symptom !== null &&
                    symptom !== undefined
                )
                .sort();
            setSymptoms(uniqueSymptoms);
        } else {
            const uniqueSymptoms = _.uniq(data.map(row => row.Symptoms))
                .filter(symptom =>
                    symptom !== "" &&
                    symptom !== null &&
                    symptom !== undefined
                )
                .sort();
            setSymptoms(uniqueSymptoms);
        }

        // Reset to first page when filters change
        setPage(0);
    }, [selectedProblem, selectedRootCause, selectedSymptom, data]);

    const metrics: Metrics = useMemo(() => {
        // Filter excluded items from static data before calculating metrics
        const filteredStaticData = staticData.filter(row =>
            row &&
            !excludedItems.includes(row.Problem) &&
            !excludedItems.includes(row['Root cause']) &&
            // Ensure the row has at least one of these fields populated
            ((row.Problem && row.Problem.trim() !== '') ||
                (row['Root cause'] && row['Root cause'].trim() !== '') ||
                (row.Symptoms && row.Symptoms.trim() !== ''))
        );

        // Static metrics
        const staticProblemCounts: Record<string, number> = {};
        filteredStaticData.forEach(row => {
            if (row.Problem) {
                staticProblemCounts[row.Problem] = (staticProblemCounts[row.Problem] || 0) + 1;
            }
        });

        const topProblemArray = Object.entries(staticProblemCounts)
            .sort(([, a], [, b]) => b - a);

        const topProblem = topProblemArray.length > 0 ?
            { name: topProblemArray[0][0], count: topProblemArray[0][1] } : null;

        const distributionData = Object.entries(staticProblemCounts)
            .map(([name, value]) => ({ name, value }))
            .sort((a, b) => b.value - a.value)
            .slice(0, 6);

        // Filtered metrics
        const total = filteredData.length;
        const aiUsed = filteredData.filter(row => row['AI Usage ID'] === 'Yes').length;
        const aiPercentage = total ? ((aiUsed / total) * 100).toFixed(1) : 0;

        return {
            total,
            aiUsed,
            aiPercentage,
            topProblem,
            distributionData
        };
    }, [staticData, filteredData]);

    const handleChangePage = (newPage: number) => {
        setPage(newPage);
    };

    const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLSelectElement>) => {
        setRowsPerPage(parseInt(event.target.value, 10));
        setPage(0);
    };

    if (loading) return (
        <div className="flex justify-center items-center h-screen">
            <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
        </div>
    );

    if (error) return (
        <div className="flex justify-center items-center h-screen">
            <p className="text-red-500">Error: {error}</p>
        </div>
    );

    return (
        <div className="overflow-y-auto">
            <div className="p-5">
                {/* Filters */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">All Issues</label>
                        <select
                            className="w-full border border-gray-300 rounded-md p-2 focus:ring-blue-500 focus:border-blue-500"
                            value={selectedProblem}
                            onChange={(e) => setSelectedProblem(e.target.value)}
                        >
                            <option value="all_problems">All Issues</option>
                            {problems.map((problem) => (
                                <option key={problem} value={problem}>{problem}</option>
                            ))}
                        </select>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">All Root Causes</label>
                        <select
                            className={`w-full border border-gray-300 rounded-md p-2 focus:ring-blue-500 focus:border-blue-500 ${!selectedProblem || selectedProblem === "all_problems" ? "opacity-50 cursor-not-allowed" : ""
                                }`}
                            value={selectedRootCause}
                            onChange={(e) => setSelectedRootCause(e.target.value)}
                            disabled={!selectedProblem || selectedProblem === "all_problems"}
                        >
                            <option value="all_causes">All Root Causes</option>
                            {rootCauses.map((cause) => (
                                <option key={cause} value={cause}>{cause}</option>
                            ))}
                        </select>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">All Symptoms</label>
                        <select
                            className={`w-full border border-gray-300 rounded-md p-2 focus:ring-blue-500 focus:border-blue-500 ${!selectedProblem || selectedProblem === "all_problems" ? "opacity-50 cursor-not-allowed" : ""
                                }`}
                            value={selectedSymptom}
                            onChange={(e) => setSelectedSymptom(e.target.value)}
                            disabled={!selectedProblem || selectedProblem === "all_problems"}
                        >
                            <option value="all_symptoms">All Symptoms</option>
                            {symptoms.map((symptom) => (
                                <option key={symptom} value={symptom}>{symptom}</option>
                            ))}
                        </select>
                    </div>
                </div>

                {/* Metric Cards */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
                    {/* Total Cases Card */}
                    <div className="bg-white rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-105">
                        <div className="bg-gradient-to-r from-blue-700 to-indigo-900 text-white text-center py-3 px-4 rounded-t-lg text-lg font-bold">
                            Total Cases
                        </div>
                        <div className="flex flex-col items-center p-4">
                            <div className="text-4xl font-bold text-blue-600 my-2">
                                {metrics.total}
                            </div>
                            <p className="text-sm text-gray-500">
                                Total cases
                            </p>
                        </div>
                    </div>

                    {/* ElevAIte Assisted Cases Card */}
                    <div className="bg-white rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-105">
                        <div className="bg-gradient-to-r from-blue-700 to-indigo-900 text-white text-center py-3 px-4 rounded-t-lg text-lg font-bold">
                            ElevAIte Assisted Cases
                        </div>
                        <div className="flex flex-col items-center p-4">
                            <div className="text-2xl font-bold text-orange-600 my-2">
                                {metrics.aiUsed} ({metrics.aiPercentage}%)
                            </div>
                            <p className="text-sm text-gray-500">
                                AI-assisted cases
                            </p>
                        </div>
                    </div>

                    {/* Top Problem Card */}
                    <div className="bg-white rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-105">
                        <div className="bg-gradient-to-r from-blue-700 to-indigo-900 text-white text-center py-3 px-4 rounded-t-lg text-lg font-bold">
                            Top Problem
                        </div>
                        <div className="flex flex-col items-center p-4">
                            {metrics.topProblem ? (
                                <>
                                    <div className="text-xl font-bold text-blue-600 my-2">
                                        {metrics.topProblem.name}
                                    </div>
                                    <p className="text-sm text-gray-500">
                                        {metrics.topProblem.count} cases
                                    </p>
                                </>
                            ) : (
                                <p className="text-gray-500">No data available</p>
                            )}
                        </div>
                    </div>
                </div>

                {/* Problem Distribution Chart */}
                <div className="bg-white rounded-xl shadow-lg mb-6">
                    <div className="bg-gradient-to-r from-blue-700 to-indigo-900 text-white text-center py-3 px-4 rounded-t-lg text-lg font-bold">
                        Problem Distribution
                    </div>
                    <div className="p-6">
                        <div className="h-96 w-full">
                            {metrics.distributionData.length > 0 ? (
                                <ResponsiveContainer width="100%" height="100%">
                                    <BarChart data={metrics.distributionData}>
                                        <XAxis dataKey="name" />
                                        <YAxis />
                                        <Tooltip content={<CustomTooltip />} />
                                        <Bar dataKey="value" fill="#4f46e5" radius={[4, 4, 0, 0]} />
                                    </BarChart>
                                </ResponsiveContainer>
                            ) : (
                                <div className="flex h-full justify-center items-center text-gray-500">
                                    No data available
                                </div>
                            )}
                        </div>
                    </div>
                </div>

                {/* Data Table */}
                <div className="bg-white rounded-xl shadow-lg overflow-hidden">
                    <div className="bg-gradient-to-r from-blue-700 to-indigo-900 text-white text-center py-3 px-4 rounded-t-lg text-lg font-bold">
                        Case Details
                    </div>
                    <div className="p-4 overflow-x-auto">
                        <table className="min-w-full divide-y divide-gray-200">
                            <thead className="bg-gray-50">
                                <tr>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Issues</th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Root Cause</th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Symptoms</th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">ElevAIte AI Usage</th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">AHT</th>
                                </tr>
                            </thead>
                            <tbody className="bg-white divide-y divide-gray-200">
                                {filteredData.length > 0 ? (
                                    filteredData
                                        .slice(page * rowsPerPage, (page + 1) * rowsPerPage)
                                        .filter(row =>
                                            // Filter out any row where all required fields are empty or null
                                            row &&
                                            (row.Problem || row['Root cause'] || row.Symptoms)
                                        )
                                        .map((row, index) => (
                                            <tr key={`${row.Problem}-${index}`} className="hover:bg-gray-50 transition-colors">
                                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{row.Problem || '-'}</td>
                                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{row['Root cause'] || '-'}</td>
                                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{row.Symptoms || '-'}</td>
                                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{row['AI Usage ID'] || '-'}</td>
                                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                                    {row['Chat Duration'] && row['Chat Duration'] !== 'N/A' ? (
                                                        <div>
                                                            <div className="font-bold">{row['Chat Duration']}</div>
                                                            <div className="text-xs text-gray-500">minutes</div>
                                                        </div>
                                                    ) : (
                                                        <div className="font-bold">N/A</div>
                                                    )}
                                                </td>
                                            </tr>
                                        ))
                                ) : (
                                    <tr>
                                        <td colSpan={5} className="px-6 py-4 text-center text-gray-500">
                                            No data available
                                        </td>
                                    </tr>
                                )}
                            </tbody>
                        </table>

                        {/* Pagination */}
                        <div className="flex items-center justify-between border-t border-gray-200 bg-white py-3">
                            <div className="flex flex-1 items-center justify-between">
                                <div>
                                    <p className="text-sm text-gray-700">
                                        Showing <span className="font-medium">{filteredData.length > 0 ? page * rowsPerPage + 1 : 0}</span> to{' '}
                                        <span className="font-medium">
                                            {Math.min((page + 1) * rowsPerPage, filteredData.length)}
                                        </span>{' '}
                                        of <span className="font-medium">{filteredData.length}</span> results
                                    </p>
                                </div>
                                <div className="flex">
                                    <select
                                        className="mr-4 border border-gray-300 rounded-md text-sm"
                                        value={rowsPerPage}
                                        onChange={handleChangeRowsPerPage}
                                    >
                                        {[10, 20, 30].map((value) => (
                                            <option key={value} value={value}>
                                                {value} rows
                                            </option>
                                        ))}
                                    </select>
                                    <div>
                                        <button
                                            onClick={() => handleChangePage(page - 1)}
                                            disabled={page === 0}
                                            className={`relative inline-flex items-center px-2 py-1 rounded-l-md border ${page === 0 ? 'border-gray-300 bg-gray-100 text-gray-400' : 'border-gray-300 bg-white text-gray-700 hover:bg-gray-50'
                                                }`}
                                        >
                                            Previous
                                        </button>
                                        <button
                                            onClick={() => handleChangePage(page + 1)}
                                            disabled={page >= Math.ceil(filteredData.length / rowsPerPage) - 1}
                                            className={`relative inline-flex items-center px-2 py-1 rounded-r-md border ${page >= Math.ceil(filteredData.length / rowsPerPage) - 1
                                                ? 'border-gray-300 bg-gray-100 text-gray-400'
                                                : 'border-gray-300 bg-white text-gray-700 hover:bg-gray-50'
                                                }`}
                                        >
                                            Next
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Problems;