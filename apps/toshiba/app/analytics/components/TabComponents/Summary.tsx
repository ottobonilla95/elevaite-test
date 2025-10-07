"use client";

import React, { useEffect, useState } from "react";
import { FiDatabase, FiPhoneCall, FiSettings, FiCpu, FiXCircle, FiClock, FiStar, FiUsers, FiFolder, FiBox, FiMessageSquare, FiBarChart2 } from "react-icons/fi";

import './Summary.scss'
import StatCard from "../SubComponents/StatCard";
import CustomLineChart from "../SubComponents/LineChart";
import CustomPieChart from "../SubComponents/PieChart";
import CustomBarChart from "../SubComponents/BarChart";
import HighlightCard from "../SubComponents/HighlightCard";
import InsightCard from "../SubComponents/InsightCard";
import {
    fetchEnhancedSummaryMetrics,
    fetchServiceRequestTrends,
    fetchMachineDistribution,
    fetchSeverityDistribution,
    fetchQueryAnalyticsMetricsEnhanced,
    fetchQueryAnalyticsHourlyUsageEnhanced,
    fetchQueryDailyTrends
} from "../../lib/actions";
import type {
    SummaryMetrics,
    TrendData,
    DistributionData,
    SeverityData
} from "../../lib/types";
import { DateFilters } from "../Tabs";
// import { title } from "process";
// import { FaAudioDescription } from "react-icons/fa";

interface EnhancedSummaryMetrics extends SummaryMetrics {
    total_queries?: number;
    avg_queries_per_day?: number;
    query_trends?: TrendData[];
}

interface ManagerFilter {
    managerId: number | null;
    managerName: string;
}

interface FSTFilter {
    fstId: number | null;
    fstName: string;
}

interface SummaryProps {
    dateFilters: DateFilters;
    managerFilter: ManagerFilter;
    fstFilter: FSTFilter;
}

const Summary: React.FC<SummaryProps> = ({ dateFilters, managerFilter, fstFilter }) => {
    const [metrics, setMetrics] = useState<EnhancedSummaryMetrics | null>(null);
    const [srTrends, setSrTrends] = useState<TrendData[]>([]);
    const [queryTrends, setQueryTrends] = useState<TrendData[]>([]);
    const [machineDistribution, setMachineDistribution] = useState<DistributionData[]>([]);
    const [severityDistribution, setSeverityDistribution] = useState<SeverityData[]>([]);
    const [totalSessions, setTotalSessions] = useState<number>(0);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadData();
    }, [dateFilters, managerFilter, fstFilter]);

    const loadData = async () => {
        try {
            setLoading(true);

            const filters = {
                start_date: dateFilters.startDate,
                end_date: dateFilters.endDate,
                manager_id: managerFilter.managerId,
                fst_id: fstFilter.fstId
            };

            console.log('Loading Summary data with filters:', filters);

            const [enhancedMetrics, srTrendsData, machineData, severityData] = await Promise.all([
                fetchEnhancedSummaryMetrics(filters),
                fetchServiceRequestTrends(filters),
                fetchMachineDistribution(filters),
                fetchSeverityDistribution(filters)
            ]);

            setMetrics(enhancedMetrics);
            setSrTrends(srTrendsData);
            setMachineDistribution(machineData);
            setSeverityDistribution(severityData);

            try {
                console.log('Loading real query trends for Summary chart...');

                const [dailyQueryData, queryMetrics] = await Promise.all([
                    fetchQueryDailyTrends(filters),
                    fetchQueryAnalyticsMetricsEnhanced(filters)
                ]);

                setQueryTrends(dailyQueryData || []);
                console.log('Real daily query trends loaded for Summary:', dailyQueryData.length, 'points');

                setTotalSessions(queryMetrics.total_sessions || 0);
                console.log('Total sessions loaded:', queryMetrics.total_sessions);

            } catch (queryError) {
                console.error('Error loading query trends for Summary:', queryError);
                setQueryTrends([]);
                setTotalSessions(0);
            }

        } catch (error) {
            console.error("Error loading data:", error);
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <div className='summary-container'>
                <div className="loading-state">
                    <div className="loading-spinner"></div>
                    <p>Loading Summary analytics...</p>
                </div>
            </div>
        );
    }

    if (!metrics) {
        return <div className="summary-container">No data available</div>;
    }

    const getFilterStatus = () => {
        if (fstFilter.fstId) {
            return {
                title: "FST Filter Active",
                name: fstFilter.fstName,
                description: `Showing data for FST: ${fstFilter.fstName}`
            };
        } else if (managerFilter.managerId) {
            return {
                title: "Manager Filter Active",
                name: managerFilter.managerName,
                description: `Showing data for ${managerFilter.managerName} team`
            };
        } else {
            return {
                title: "All Technicians",
                name: "No Filter",
                description: "Showing data for all technicians"
            };
        }
    };

    const filterStatus = getFilterStatus();

    const insightsData = [
        {
            icon: <FiPhoneCall />,
            title: "Total Service Requests",
            value: metrics.total_srs.toLocaleString(),
            description: `Total of ${metrics.total_srs.toLocaleString()} service requests processed`,
        },
        {
            icon: <FiMessageSquare />,
            title: "Total Queries",
            value: metrics.total_queries?.toLocaleString() || "0",
            description: `${metrics.total_queries?.toLocaleString() || "0"} queries handled across all channels`,
        },
        {
            icon: <FiMessageSquare />,
            title: "Avg. Queries per Day",
            value: metrics.avg_queries_per_day?.toString() || "0",
            description: "Across all query channels",
        },
        // {
        //     icon: <FiUsers />,
        //     title: filterStatus.title,
        //     value: filterStatus.name,
        //     description: filterStatus.description,
        // },
    ];

    const statCardData = [
        {
            icon: <FiClock />,
            label: "Avg Resolution Time",
            value: `${metrics.avg_resolution_time} days`,
            trend: "Average time to resolve SRs",
        },
        {
            icon: <FiPhoneCall />,
            label: "Avg. SRs per Day",
            value: metrics.avg_requests_per_day.toString(),
            trend: metrics.date_range.start && metrics.date_range.end
                ? `${new Date(metrics.date_range.start).toLocaleDateString()} - ${new Date(metrics.date_range.end).toLocaleDateString()}`
                : "Based on available data",
        },
        {
            icon: <FiCpu />,
            label: "Top Machine Type",
            value: metrics.top_machine_type,
            trend: `${metrics.top_machine_type} is the most serviced type`,
        },
        {
            icon: <FiBarChart2 />,
            label: "Total Sessions",
            value: totalSessions.toLocaleString(),
            trend: "Unique user sessions",
        },
    ];

    const pieChartData = machineDistribution.map((item, index) => ({
        name: item.name,
        value: item.value,
        color: ["#FF681F", "#FF9F71", "#FFD971", "#BF0909", "#FFBD71", "#FF0000"][index] || "#CCCCCC"
    }));

    const severityOrder = ['Critical', 'High', 'Medium', 'Low'];
    const barChartData = severityOrder
        .map(level => severityDistribution.find(item => item.label === level))
        .filter(item => item)
        .map(item => ({
            label: item!.label,
            count: item!.count,
            color: item!.color
        }));

    const getChartFilterBadge = () => {
        if (fstFilter.fstId) return "(FST FILTERED)";
        if (managerFilter.managerId) return "(MANAGER FILTERED)";
        return "";
    };

    const filterBadge = getChartFilterBadge();

    return (
        <div className="summary-container">
            <div className="insight-container">
                <h2><strong>Key Insights - Service Requests & Query Analytics</strong></h2>
                <div className="insight-tab">
                    {insightsData.map((item, index) => (
                        <InsightCard
                            key={index}
                            icon={item.icon}
                            title={item.title}
                            value={item.value}
                            description={item.description}
                        />
                    ))}
                </div>
            </div>

            <div className="machine-summary-container">
                <h2><strong>Service Requests & Query Summary</strong></h2>
                <div className="machine-summary-tab">
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

                <div className="summary-charts">
                    <div className="chart-box">
                        <h4>Service Requests Trend {filterBadge}</h4>
                        <div className="chart-wrapper">
                            <CustomLineChart
                                data={srTrends}
                                YAxislabel="Service Requests"
                            />
                        </div>
                    </div>
                    <div className="chart-box">
                        <h4>Query Volume Trend</h4>
                        <div className="chart-wrapper">
                            <CustomLineChart
                                data={queryTrends.length > 0 ? queryTrends : (metrics.query_trends || [])}
                                YAxislabel="Queries"
                            />
                        </div>
                    </div>
                    <div className="chart-box">
                        <h4>Machine Types Distribution {filterBadge}</h4>
                        <div className="chart-wrapper">
                            <CustomPieChart data={pieChartData} />
                        </div>
                    </div>
                    <div className="chart-box">
                        <h4>Service Requests by Severity {filterBadge}</h4>
                        <div className="chart-wrapper">
                            <CustomBarChart data={barChartData} />
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};


export default Summary;
