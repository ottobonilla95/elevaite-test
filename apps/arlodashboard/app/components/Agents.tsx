import React, { useState, useEffect, useCallback, useMemo } from 'react';
import axios from 'axios';
import _ from 'lodash';
import {
    LineChart,
    Line,
    XAxis,
    YAxis,
    Tooltip,
    Legend,
    ResponsiveContainer
} from 'recharts';

// TypeScript interfaces
interface DateRange {
    fromDate: string;
    toDate: string;
}

interface AgentDashboardProps {
    dateRange: DateRange | null;
}

interface AgentData {
    'Owner: Full Name': string;
    'Status'?: string;
    'Chat Duration': string;
    'Created Date': string;
    'AIAssisted': string;
}

interface AgentMetrics {
    aht: string;
}

interface Agent {
    name: string;
    metrics: {
        ai: AgentMetrics;
        nonAi: AgentMetrics;
    };
    aiUsagePercentage: number;
    totalTickets: number;
    performanceScore: number;
}

interface TimeData {
    date: string;
    month: string;
    year: string;
    aiAHT: number;
    nonAiAHT: number;
    ticketCount: number;
}

interface DashboardData {
    agents: Agent[];
    overallMetrics: {
        aiMetrics: AgentMetrics;
        nonAiMetrics: AgentMetrics;
        aiUsagePercentage: number;
        handleTimeData: TimeData[];
    };
}

// Helper functions
const formatPercentage = (value: number | null): string => {
    if (value === null) return 'N/A';
    if (!value && value !== 0) return '0.0%';
    return `${Number(value).toFixed(1)}%`;
};

const safeNumberFormat = (value: number | string | null, decimals = 1): string => {
    if (value === null) return '0.0';
    const num = parseFloat(value as string);
    return isNaN(num) ? '0.0' : num.toFixed(decimals);
};

const calculatePerformanceScore = (aiUsagePercentage: number): number => {
    return aiUsagePercentage || 0;
};

// Calculate AHT helper
const calculateAHT = (durations: string[]): string => {
    if (!durations || !durations.length) return '0:00';

    const totalSeconds = durations.reduce((sum, duration) => {
        if (!duration) return sum;
        try {
            const [mins, secs] = duration.split(':').map(str => {
                const num = parseInt(str, 10);
                return isNaN(num) ? 0 : num;
            });
            return sum + (mins * 60) + (secs || 0);
        } catch (err) {
            console.error('Error processing duration:', duration);
            return sum;
        }
    }, 0);

    const avgSeconds = Math.round(totalSeconds / durations.length);
    const mins = Math.floor(avgSeconds / 60);
    const secs = avgSeconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
};

// Convert time string to minutes for chart data
const convertTimeToMinutes = (timeStr: string): number => {
    if (!timeStr || timeStr === 'N/A') return 0;
    try {
        const [mins, secs] = timeStr.split(':').map(Number);
        return mins + (secs / 60);
    } catch {
        return 0;
    }
};

// Function to handle Excel date conversion
const excelDateToJSDate = (excelDate: number): Date | null => {
    // Excel's epoch starts on Jan 1, 1900, but JavaScript's epoch starts on Jan 1, 1970
    if (typeof excelDate === 'number') {
        const millisecondsPerDay = 24 * 60 * 60 * 1000;
        // Excel has a leap year bug where it counts 1900 as a leap year
        // If the date is greater than 60 (February 29, 1900), subtract 1
        const adjustedExcelDate = excelDate > 60 ? excelDate - 1 : excelDate;
        // Convert to JavaScript date (add days to the JavaScript epoch)
        return new Date((adjustedExcelDate - 25569) * millisecondsPerDay);
    }
    return null;
};

// Function to clean up data received from API
const cleanApiData = (apiData: AgentData[]): AgentData[] => {
    return apiData.map(item => {
        // Make a copy of the item to avoid modifying the original
        const cleanedItem = { ...item };

        // Handle 'Created Date' field
        if (cleanedItem['Created Date']) {
            // If it's a number (Excel serial date)
            if (typeof cleanedItem['Created Date'] === 'number') {
                const jsDate = excelDateToJSDate(cleanedItem['Created Date']);
                if (jsDate) {
                    cleanedItem['Created Date'] = jsDate.toISOString().split('T')[0]; // Format as YYYY-MM-DD
                }
            }
            // If it's already a string but in an unusual format
            else if (typeof cleanedItem['Created Date'] === 'string') {
                // Try to detect format and convert if needed
                if (cleanedItem['Created Date'].includes('/')) {
                    // Handle MM/DD/YYYY format
                    const parts = cleanedItem['Created Date'].split('/');
                    if (parts.length === 3) {
                        // Convert to YYYY-MM-DD
                        cleanedItem['Created Date'] = `${parts[2]}-${parts[0].padStart(2, '0')}-${parts[1].padStart(2, '0')}`;
                    }
                }
                // For February 25 or December 24 formats
                else if (cleanedItem['Created Date'].toLowerCase().includes('february')) {
                    // Assume 2025 for February
                    const day = cleanedItem['Created Date'].match(/\d+/);
                    if (day) {
                        cleanedItem['Created Date'] = `2025-02-${day[0].padStart(2, '0')}`;
                    }
                }
                else if (cleanedItem['Created Date'].toLowerCase().includes('december')) {
                    // Assume 2024 for December
                    const day = cleanedItem['Created Date'].match(/\d+/);
                    if (day) {
                        cleanedItem['Created Date'] = `2024-12-${day[0].padStart(2, '0')}`;
                    }
                }
                else if (cleanedItem['Created Date'].toLowerCase().includes('january')) {
                    // Assume 2025 for January
                    const day = cleanedItem['Created Date'].match(/\d+/);
                    if (day) {
                        cleanedItem['Created Date'] = `2025-01-${day[0].padStart(2, '0')}`;
                    }
                }
            }
        }

        // Handle 'AIAssisted' field for consistency
        if ('AIAssisted' in cleanedItem) {
            const value = String(cleanedItem['AIAssisted']).toLowerCase();
            cleanedItem['AIAssisted'] = (value === 'yes' || value === 'y' || value === 'true' || value === '1') ? 'Yes' : 'No';
        }

        // Handle 'Chat Duration' field for consistency
        if (cleanedItem['Chat Duration']) {
            // If it's a number (seconds), convert to MM:SS format
            if (typeof cleanedItem['Chat Duration'] === 'number') {
                const minutes = Math.floor(cleanedItem['Chat Duration'] / 60);
                const seconds = Math.floor(cleanedItem['Chat Duration'] % 60);
                cleanedItem['Chat Duration'] = `${minutes}:${seconds.toString().padStart(2, '0')}`;
            }
            // If it's already a string but not in MM:SS format (e.g., "5.5")
            else if (typeof cleanedItem['Chat Duration'] === 'string' && !cleanedItem['Chat Duration'].includes(':')) {
                const totalSeconds = parseFloat(cleanedItem['Chat Duration']) * 60; // Assume minutes
                const minutes = Math.floor(totalSeconds / 60);
                const seconds = Math.floor(totalSeconds % 60);
                cleanedItem['Chat Duration'] = `${minutes}:${seconds.toString().padStart(2, '0')}`;
            }
        }

        return cleanedItem;
    });
};

const AgentDashboard: React.FC<AgentDashboardProps> = ({ dateRange }) => {
    // States
    const [data, setData] = useState<DashboardData>({
        agents: [],
        overallMetrics: {
            aiMetrics: {
                aht: '0:00'
            },
            nonAiMetrics: {
                aht: '0:00'
            },
            aiUsagePercentage: 0,
            handleTimeData: []
        }
    });
    const [loading, setLoading] = useState<boolean>(true);
    const [searchTerm, setSearchTerm] = useState<string>('');
    const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);
    const [detailsOpen, setDetailsOpen] = useState<boolean>(false);
    const [error, setError] = useState<string | null>(null);

    // Data processing logic
    const processData = useCallback((rawData: AgentData[]) => {
        try {
            console.log("Processing data:", rawData.length, "entries");

            // Clean the data to ensure consistent formats
            const cleanedData = cleanApiData(rawData);
            console.log("Data cleaned for processing");

            // Process the input data
            const validData = cleanedData.map(item => ({
                name: item['Owner: Full Name'] || 'Unknown',
                status: item['Status'],
                duration: item['Chat Duration'] || '0:00',
                createdDate: item['Created Date'],
                aiAssisted: item['AIAssisted'] === 'Yes'
            })).filter(item => item.name !== 'Unknown');

            console.log(`Processing ${validData.length} valid data entries`);

            // Group by agent name
            const byAgent = _.groupBy(validData, 'name');

            // Process each agent's data
            const agents = Object.entries(byAgent).map(([name, tickets]) => {
                const aiTickets = tickets.filter(t => t.aiAssisted);
                const nonAiTickets = tickets.filter(t => !t.aiAssisted);
                const hasAiTickets = aiTickets.length > 0;

                // Calculate the performance score (based on AI usage)
                const aiUsagePercentage = tickets.length ? (aiTickets.length / tickets.length) * 100 : 0;
                const performanceScore = calculatePerformanceScore(aiUsagePercentage);

                return {
                    name,
                    metrics: {
                        ai: {
                            aht: hasAiTickets ? calculateAHT(aiTickets.map((t: any) => t.duration)) : 'N/A'
                        },
                        nonAi: {
                            aht: calculateAHT(nonAiTickets.map((t: any) => t.duration))
                        }
                    },
                    aiUsagePercentage,
                    totalTickets: tickets.length,
                    performanceScore
                };
            });

            // Calculate overall metrics
            const allAiTickets = validData.filter(t => t.aiAssisted);
            const allNonAiTickets = validData.filter(t => !t.aiAssisted);

            // Process handle time data by period (day/week/month based on date range)
            const handleTimeData = (() => {
                console.log('Processing time series data with dynamic granularity');

                try {
                    // Initialize filteredData from validData
                    let filteredData = validData;
                    console.log(`Starting with ${validData.length} total tickets`);

                    // Log some sample date formats for debugging
                    const sampleDates = validData.slice(0, 5).map(t => t.createdDate);
                    console.log('Sample date formats in data:', sampleDates);

                    // Apply date filtering if a date range is provided
                    if (dateRange && dateRange.fromDate && dateRange.toDate) {
                        const fromDate = new Date(dateRange.fromDate);
                        const toDate = new Date(dateRange.toDate);

                        // Add one day to toDate to include the end date
                        toDate.setDate(toDate.getDate() + 1);

                        console.log(`Date range: ${fromDate.toISOString()} to ${toDate.toISOString()}`);

                        filteredData = validData.filter(ticket => {
                            if (!ticket.createdDate) return false;

                            try {
                                const ticketDate = new Date(ticket.createdDate);
                                return ticketDate >= fromDate && ticketDate < toDate;
                            } catch (e) {
                                return false;
                            }
                        });

                        console.log(`Date filtered: ${filteredData.length} out of ${validData.length} tickets`);
                    }

                    // CRITICAL FIX: If no data passed the filter but we had valid data, use all the data
                    if (filteredData.length === 0 && validData.length > 0) {
                        console.log('No data passed the filter, using all valid data instead');
                        filteredData = validData;
                    }

                    if (filteredData.length === 0) {
                        console.log('No data available for chart after filtering');
                        return [];
                    }

                    // Determine the appropriate granularity based on date range
                    let granularity: 'day' | 'week' | 'month' = 'month'; // Default to month

                    if (dateRange && dateRange.fromDate && dateRange.toDate) {
                        const fromDate = new Date(dateRange.fromDate);
                        const toDate = new Date(dateRange.toDate);
                        const daysDiff = Math.ceil((toDate.getTime() - fromDate.getTime()) / (1000 * 60 * 60 * 24));

                        console.log(`Date range spans ${daysDiff} days`);

                        if (daysDiff <= 14) {
                            granularity = 'day';
                        } else if (daysDiff <= 60) {
                            granularity = 'week';
                        } else {
                            granularity = 'month';
                        }
                    } else {
                        // If no date range, determine granularity based on data span
                        const sortedDates = filteredData
                            .filter(ticket => ticket.createdDate)
                            .map(ticket => new Date(ticket.createdDate))
                            .sort((a, b) => a.getTime() - b.getTime());

                        if (sortedDates.length >= 2) {
                            const earliestDate = sortedDates[0];
                            const latestDate = sortedDates[sortedDates.length - 1];
                            const daysDiff = Math.ceil((latestDate.getTime() - earliestDate.getTime()) / (1000 * 60 * 60 * 24));

                            console.log(`Data spans ${daysDiff} days`);

                            if (daysDiff <= 14) {
                                granularity = 'day';
                            } else if (daysDiff <= 60) {
                                granularity = 'week';
                            } else {
                                granularity = 'month';
                            }
                        }
                    }

                    console.log(`Using ${granularity} granularity for chart`);

                    // Group data by the appropriate time unit
                    const groupedData = {};

                    filteredData.forEach(ticket => {
                        if (!ticket.createdDate) return;

                        try {
                            let key;
                            let displayLabel;
                            const date = new Date(ticket.createdDate);

                            if (isNaN(date.getTime())) {
                                return;
                            }

                            if (granularity === 'day') {
                                // Use the full date as the key: 2024-12-15
                                key = date.toISOString().substring(0, 10);
                                // Display as: Dec 15
                                displayLabel = `${date.toLocaleString('en-us', { month: 'short' })} ${date.getDate()}`;
                            } else if (granularity === 'week') {
                                // Week-based grouping
                                // Get the first day of the month
                                const firstDay = new Date(date.getFullYear(), date.getMonth(), 1);
                                // Calculate days since the first day of the month plus offset for first day of week
                                const daysSinceFirstOfMonth = date.getDate() - 1 + firstDay.getDay();
                                // Calculate week number (1-indexed)
                                const weekNum = Math.ceil((daysSinceFirstOfMonth + 1) / 7);

                                key = `${date.getFullYear()}-${date.getMonth() + 1}-W${weekNum}`;
                                // Display as: Dec W3
                                displayLabel = `${date.toLocaleString('en-us', { month: 'short' })} W${weekNum}`;
                            } else {
                                // Month-based grouping
                                key = `${date.getFullYear()}-${date.getMonth() + 1}`;
                                // Display as: Dec 2024
                                displayLabel = date.toLocaleString('en-us', { month: 'short', year: 'numeric' });
                            }

                            if (!groupedData[key]) {
                                groupedData[key] = {
                                    key,
                                    displayLabel,
                                    aiTickets: [],
                                    nonAiTickets: []
                                };
                            }

                            if (ticket.aiAssisted) {
                                groupedData[key].aiTickets.push(ticket);
                            } else {
                                groupedData[key].nonAiTickets.push(ticket);
                            }
                        } catch (e) {
                            console.warn('Error processing ticket date', e);
                        }
                    });

                    // Convert grouped data to chart format
                    const result = Object.values(groupedData).map((group: any) => ({
                        date: group.key,
                        month: group.displayLabel,
                        year: '',
                        aiAHT: convertTimeToMinutes(calculateAHT(group.aiTickets.map((t: any) => t.duration))),
                        nonAiAHT: convertTimeToMinutes(calculateAHT(group.nonAiTickets.map((t: any) => t.duration))),
                        ticketCount: group.aiTickets.length + group.nonAiTickets.length
                    }));

                    // Sort chronologically
                    result.sort((a, b) => a.date.localeCompare(b.date));

                    console.log(`Generated ${result.length} data points for chart with ${granularity} granularity`);
                    return result;
                } catch (err) {
                    console.error('Error generating chart data:', err);
                    // Return empty array on error
                    return [];
                }
            })();
            // Calculate overall metrics
            const overallMetrics = {
                aiMetrics: {
                    aht: calculateAHT(allAiTickets.map(t => t.duration))
                },
                nonAiMetrics: {
                    aht: calculateAHT(allNonAiTickets.map(t => t.duration))
                },
                aiUsagePercentage: validData.length ? (allAiTickets.length / validData.length) * 100 : 0,
                handleTimeData: handleTimeData
            };

            // Sort agents by performance score and update state
            const sortedAgents = _.orderBy(agents, ['performanceScore'], ['desc']);
            setData({
                agents: sortedAgents,
                overallMetrics
            });
            setLoading(false);
            console.log("Data processing completed. Total tickets:", validData.length);
            console.log("AI tickets:", allAiTickets.length, "Non-AI tickets:", allNonAiTickets.length);
            console.log("AI usage percentage:", overallMetrics.aiUsagePercentage.toFixed(1) + "%");

        } catch (err: any) {
            console.error('Data processing error:', err);
            setError(err.message);
            setLoading(false);
        }
    }, [dateRange]);

    // Filtered agents computation
    const filteredAgents = useMemo(() => {
        if (!searchTerm.trim()) {
            // Show top 3 by performance score
            return data.agents.slice(0, 3);
        }
        return data.agents.filter(agent =>
            agent.name.toLowerCase().includes(searchTerm.toLowerCase())
        );
    }, [data.agents, searchTerm]);

    // Data fetching
    useEffect(() => {
        const fetchData = async () => {
            setLoading(true);
            setError(null);

            try {
                let response;
                let gotData = false;

                // Try to fetch data using date range if provided
                if (dateRange && dateRange.fromDate && dateRange.toDate) {
                    console.log(`Fetching data for date range: ${dateRange.fromDate} to ${dateRange.toDate}`);

                    try {
                        // First try with from_date/to_date parameters
                        response = await axios.get('http://localhost:5000/api/agents-data', {
                            params: {
                                from_date: dateRange.fromDate,
                                to_date: dateRange.toDate
                            }
                        });
                        console.log('Successfully fetched data using from_date/to_date params');

                        if (response.data && response.data.length > 0) {
                            processData(response.data);
                            gotData = true;
                        }
                    } catch (err) {
                        console.warn('Failed to fetch with from_date/to_date, trying with from/to...');

                        // Then try with from/to parameters
                        try {
                            response = await axios.get('http://localhost:5000/api/agents-data', {
                                params: {
                                    from: dateRange.fromDate,
                                    to: dateRange.toDate
                                }
                            });
                            console.log('Successfully fetched data using from/to params');

                            if (response.data && response.data.length > 0) {
                                processData(response.data);
                                gotData = true;
                            }
                        } catch (innerErr) {
                            console.error('Failed to fetch with from/to as well');
                        }
                    }
                }

                // If no date range or no data found with date range, fetch all data
                if (!gotData) {
                    console.log('Fetching all data (no date range or no data found with date filter)');
                    response = await axios.get('http://localhost:5000/api/agents-data');
                    console.log('Successfully fetched all data');

                    if (response.data && response.data.length > 0) {
                        processData(response.data);
                        gotData = true;
                    } else {
                        setError('No data available');
                        setLoading(false);
                    }
                }
            } catch (err) {
                console.error('All fetch attempts failed:', err);
                setError('Failed to fetch data. Please try again later.');
                setLoading(false);
            }
        };

        fetchData();
    }, [dateRange, processData]);
    // Render loading state
    if (loading) {
        return (
            <div className="flex justify-center items-center h-screen bg-gray-50">
                <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-indigo-600"></div>
            </div>
        );
    }

    // Render error state
    if (error) {
        return (
            <div className="flex justify-center items-center h-screen bg-gray-50 text-red-600">
                <div>Error: {error}</div>
            </div>
        );
    }

    return (
        <div className="py-4 px-4 sm:px-6 lg:px-8 bg-gray-50 min-h-screen">
            <div className="max-w-7xl mx-auto">
                <h1 className="text-2xl font-bold text-gray-900 mb-6">
                    Agent Performance Dashboard
                </h1>

                {/* Search Bar */}
                <div className="mb-4">
                    <div className="relative max-w-md">
                        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-gray-400" viewBox="0 0 20 20" fill="currentColor">
                                <path fillRule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clipRule="evenodd" />
                            </svg>
                        </div>
                        <input
                            type="text"
                            placeholder="Search agents..."
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                        />
                    </div>
                </div>

                {/* Main Dashboard Layout */}
                <div className="grid grid-cols-1 lg:grid-cols-4 gap-0 mb-6">
                    {/* Handle Time Trends Chart */}
                    <div className="lg:col-span-3 bg-white rounded-tl-xl rounded-bl-xl shadow-sm border border-gray-200">
                        <div className="bg-indigo-600 p-4 rounded-tl-xl">
                            <h3 className="text-white font-semibold text-lg">Handle Time Trends</h3>
                            {dateRange && (
                                <p className="text-white text-sm opacity-80">
                                    {new Date(dateRange.fromDate).toLocaleDateString()} - {new Date(dateRange.toDate).toLocaleDateString()}
                                </p>
                            )}
                        </div>
                        <div className="p-4">
                            <div className="h-80 w-full">
                                <ResponsiveContainer width="100%" height="100%">
                                    <LineChart
                                        data={data.overallMetrics.handleTimeData}
                                        margin={{ top: 10, right: 10, left: 10, bottom: 30 }}
                                    >
                                        <XAxis
                                            dataKey="month"
                                            angle={-45}
                                            textAnchor="end"
                                            height={60}
                                            tick={{ fontSize: 12 }}
                                            tickMargin={5}
                                        />
                                        <YAxis
                                            label={{
                                                value: 'Handle Time (MM:SS)',
                                                angle: -90,
                                                position: 'insideLeft',
                                                style: { textAnchor: 'middle', fill: '#666', fontSize: 12 }
                                            }}
                                            tickFormatter={(value) => {
                                                const mins = Math.floor(value);
                                                const secs = Math.round((value % 1) * 60);
                                                return `${mins}:${secs.toString().padStart(2, '0')}`;
                                            }}
                                        />
                                        <Tooltip
                                            formatter={(value: any) => {
                                                const mins = Math.floor(value);
                                                const secs = Math.round((value % 1) * 60);
                                                return [`${mins}:${secs.toString().padStart(2, '0')}`, ''];
                                            }}
                                        />
                                        <Legend
                                            iconType="circle"
                                            iconSize={10}
                                            verticalAlign="bottom"
                                        />
                                        {/* Non-AI line first (red) */}
                                        <Line
                                            type="monotone"
                                            dataKey="nonAiAHT"
                                            name="Non-AI Handle Time"
                                            stroke="#DC2626"
                                            strokeWidth={2}
                                            dot={{ r: 5, fill: "#DC2626" }}
                                            activeDot={{ r: 8 }}
                                        />
                                        {/* AI line second (green) */}
                                        <Line
                                            type="monotone"
                                            dataKey="aiAHT"
                                            name="AI Handle Time"
                                            stroke="#059669"
                                            strokeWidth={2}
                                            dot={{ r: 5, fill: "#059669" }}
                                            activeDot={{ r: 8 }}
                                        />
                                    </LineChart>
                                </ResponsiveContainer>
                            </div>
                        </div>
                    </div>

                    {/* Metrics Cards */}
                    <div className="lg:col-span-1">
                        <div className="grid grid-cols-1 gap-0">
                            {/* AI Usage Card */}
                            <div className="bg-white rounded-tr-xl border border-l-0 border-gray-200 p-4">
                                <div className="text-gray-600 text-sm font-medium mb-1">AI Usage</div>
                                <div className="font-bold text-3xl text-emerald-600">
                                    {formatPercentage(data.overallMetrics.aiUsagePercentage)}
                                </div>
                            </div>
                            {/* Overall AI Handle Time Card */}
                            <div className="bg-white border border-l-0 border-t-0 border-gray-200 p-4">
                                <div className="text-gray-600 text-sm font-medium mb-1">AI Handle Time</div>
                                <div className="font-bold text-3xl text-amber-500">
                                    {data.overallMetrics.aiMetrics.aht}
                                </div>
                            </div>
                            {/* Overall Non-AI Handle Time Card */}
                            <div className="bg-white rounded-br-xl border border-l-0 border-t-0 border-gray-200 p-4">
                                <div className="text-gray-600 text-sm font-medium mb-1">Non-AI Handle Time</div>
                                <div className="font-bold text-3xl text-indigo-600">
                                    {data.overallMetrics.nonAiMetrics.aht}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Agent List Title */}
                <div className="flex justify-between items-center mb-4">
                    <h2 className="text-xl font-semibold text-gray-900">
                        {searchTerm ? 'Search Results' : 'Top Performing Agents'}
                    </h2>
                </div>

                {/* Agent Cards */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {filteredAgents.length > 0 ? (
                        filteredAgents.map((agent, index) => (
                            <div key={agent.name} className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden hover:shadow-md transition-all duration-300 hover:-translate-y-1">
                                <div className="p-5">
                                    {/* Agent Header */}
                                    <div className="flex items-center mb-4">
                                        <div className={`w-14 h-14 rounded-full flex items-center justify-center text-white text-xl font-semibold mr-4 ${index === 0 ? 'bg-amber-500' : 'bg-indigo-600'}`}>
                                            {agent.name[0]}
                                        </div>
                                        <div>
                                            <h3 className="text-lg font-semibold text-gray-900">{agent.name}</h3>
                                            <p className="text-sm text-gray-500">
                                                Performance Score: {agent.performanceScore.toFixed(1)}
                                            </p>
                                        </div>
                                    </div>

                                    {/* AI Usage Info */}
                                    <div className="bg-gray-50 p-4 rounded-lg mb-4">
                                        <div className="grid grid-cols-2 gap-4">
                                            <div>
                                                <p className="text-lg font-semibold text-emerald-600">
                                                    {formatPercentage(agent.aiUsagePercentage)}
                                                </p>
                                            </div>
                                            <div>
                                                <p className="text-xs text-gray-500 mb-1">Handle Time</p>
                                                <p className="text-sm text-emerald-600">
                                                    AI: {agent.metrics.ai.aht}
                                                </p>
                                                <p className="text-sm text-red-600">
                                                    Non-AI: {agent.metrics.nonAi.aht}
                                                </p>
                                            </div>
                                        </div>
                                    </div>

                                    {/* Details Button */}
                                    <button
                                        onClick={() => {
                                            setSelectedAgent(agent);
                                            setDetailsOpen(true);
                                        }}
                                        className="w-full bg-gradient-to-r from-indigo-600 to-indigo-500 text-white py-2 px-4 rounded-lg hover:from-indigo-700 hover:to-indigo-600 transition-colors duration-300 font-medium"
                                    >
                                        View Details
                                    </button>
                                </div>
                            </div>
                        ))
                    ) : (
                        <div className="col-span-3 bg-white p-8 text-center rounded-xl shadow-sm border border-gray-200">
                            <p className="text-gray-500 text-lg">
                                No agents found matching your search criteria
                            </p>
                        </div>
                    )}
                </div>

                {/* Agent Details Modal */}
                {detailsOpen && selectedAgent && (
                    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
                        <div className="bg-white rounded-xl shadow-xl w-full max-w-5xl max-h-[90vh] overflow-y-auto">
                            {/* Modal Header */}
                            <div className="bg-gradient-to-r from-indigo-600 to-indigo-400 p-5 flex justify-between items-center">
                                <div className="flex items-center space-x-4">
                                    <div className="w-14 h-14 rounded-full bg-white flex items-center justify-center text-indigo-600 text-xl font-semibold">
                                        {selectedAgent.name[0]}
                                    </div>
                                    <div>
                                        <h2 className="text-xl font-semibold text-white">
                                            {selectedAgent.name}
                                        </h2>
                                        <p className="text-indigo-100">Performance Details</p>
                                    </div>
                                </div>
                                <button
                                    onClick={() => setDetailsOpen(false)}
                                    className="text-white hover:bg-indigo-700 rounded-full p-2"
                                >
                                    <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" viewBox="0 0 20 20" fill="currentColor">
                                        <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                                    </svg>
                                </button>
                            </div>

                            {/* Modal Content */}
                            <div className="p-6">
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                                    {/* AI Usage Card */}
                                    <div className="bg-white rounded-xl shadow-sm p-4 border border-gray-200 hover:shadow-md transition-all duration-300">
                                        <div className="text-gray-500 text-sm font-medium mb-3">AI Usage</div>
                                        <div className="font-bold text-2xl text-emerald-600">
                                            {formatPercentage(selectedAgent.aiUsagePercentage)}
                                        </div>
                                        <div className="text-sm text-gray-500 mt-2">
                                            {selectedAgent.totalTickets} total tickets
                                        </div>
                                    </div>

                                    {/* Handle Time Comparison */}
                                    <div className="bg-white rounded-xl shadow-sm p-4 border border-gray-200 hover:shadow-md transition-all duration-300">
                                        <div className="text-gray-500 text-sm font-medium mb-3">Handle Time</div>
                                        <div className="grid grid-cols-2 gap-4">
                                            <div>
                                                <div className="text-emerald-600 font-semibold text-sm mb-1">With AI</div>
                                                <div className="text-emerald-600 font-bold text-xl">
                                                    {selectedAgent.metrics.ai.aht}
                                                </div>
                                            </div>
                                            <div>
                                                <div className="text-red-600 font-semibold text-sm mb-1">Without AI</div>
                                                <div className="text-red-600 font-bold text-xl">
                                                    {selectedAgent.metrics.nonAi.aht}
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                {/* Performance Analysis Section */}
                                <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                                    <h3 className="text-lg font-semibold text-gray-900 mb-4">
                                        Performance Analysis
                                    </h3>
                                    <div>
                                        <h4 className="text-sm font-medium text-gray-500 mb-2">
                                            AI Usage Impact
                                        </h4>
                                        <p className="text-gray-700">
                                            {selectedAgent.name} utilizes AI assistance in {formatPercentage(selectedAgent.aiUsagePercentage)} of tickets,
                                            with an average handle time of {selectedAgent.metrics.ai.aht} for AI-assisted tickets compared to {' '}
                                            {selectedAgent.metrics.nonAi.aht} for non-AI tickets.
                                            {selectedAgent.metrics.ai.aht !== 'N/A' && selectedAgent.metrics.nonAi.aht !== '0:00' ? (
                                                (() => {
                                                    const aiTime = selectedAgent.metrics.ai.aht.split(':').map(Number);
                                                    const nonAiTime = selectedAgent.metrics.nonAi.aht.split(':').map(Number);
                                                    const aiSeconds = aiTime[0] * 60 + aiTime[1];
                                                    const nonAiSeconds = nonAiTime[0] * 60 + nonAiTime[1];

                                                    if (aiSeconds < nonAiSeconds) {
                                                        const savingsPercent = ((nonAiSeconds - aiSeconds) / nonAiSeconds * 100).toFixed(1);
                                                        return ` This represents a time savings of ${savingsPercent}% when using AI assistance.`;
                                                    }
                                                    return '';
                                                })()
                                            ) : ''}
                                        </p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default AgentDashboard;