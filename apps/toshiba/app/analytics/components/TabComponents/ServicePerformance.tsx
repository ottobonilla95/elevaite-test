"use client";

import React, { useState, useEffect } from 'react';
import { FiPhoneCall, FiClock, FiTool, FiTrendingUp, FiHardDrive, FiSettings } from 'react-icons/fi';

import './ServicePerformance.scss';
import StatCard from '../SubComponents/StatCard';
import CustomBarChart from '../SubComponents/BarChart';
import CustomLineChart from '../SubComponents/LineChart';
import CustomPieChart from '../SubComponents/PieChart';
import ReverseBarChart from '../SubComponents/ReverseBarChart';

import {
    fetchServiceMetrics,
    fetchTravelByRegion,
    fetchTechnicianPerformance,
    fetchTimeAnalysis,
    fetchTopCustomers,
    fetchSeverityDistribution,
    fetchMachineDistribution,
    fetchServiceRequestTrends,
    fetchIssueCategories,
    fetchServiceMachineDistribution
} from '../../lib/actions';

import {
    DateFilters,
    ServiceMetrics,
    RegionTravelTime,
    TechnicianPerformance,
    TimeAnalysis,
    CustomerData,
    SeverityData,
    DistributionData,
    TrendData,
    CategoryBarData
} from '../../lib/types';

interface ServicePerformanceProps {
    dateFilters: DateFilters;
}

const ServicePerformance: React.FC<ServicePerformanceProps> = ({ dateFilters }) => {
    const [loading, setLoading] = useState(true);
    const [metrics, setMetrics] = useState<ServiceMetrics | null>(null);
    const [timeAnalysis, setTimeAnalysis] = useState<TimeAnalysis | null>(null);
    const [customers, setCustomers] = useState<CustomerData[]>([]);
    const [severityData, setSeverityData] = useState<SeverityData[]>([]);
    const [machineDistribution, setMachineDistribution] = useState<any[]>([]);
    const [trendData, setTrendData] = useState<TrendData[]>([]);
    const [formattedTrends, setFormattedTrends] = useState<TrendData[]>([]);
    const [issueCategories, setIssueCategories] = useState<CategoryBarData[]>([]);
    const [technicianPerformance, setTechnicianPerformance] = useState<TechnicianPerformance[]>([]);

    const [selectedCustomer, setSelectedCustomer] = useState<string>("");
    const [selectedCustomerData, setSelectedCustomerData] = useState<CustomerData | null>(null);

    const formatTime = (hours: number): string => {
        if (!hours || hours === 0) return "0h 0m";
        const h = Math.floor(hours);
        const m = Math.round((hours - h) * 60);
        return `${h}h ${m}m`;
    };

    const formatTrendDates = (data: TrendData[]): TrendData[] => {
        if (!data || data.length === 0) return data;

        const sortedData = [...data].sort((a, b) => {
            return new Date(a.date).getTime() - new Date(b.date).getTime();
        });

        const dateStrings = sortedData.map(item => item.date);
        const isYearlyData = dateStrings.every(date => date.endsWith('-01-01'));
        const isMonthlyData = !isYearlyData && dateStrings.every(date => date.endsWith('-01'));

        return sortedData.map(item => {
            const date = new Date(item.date);

            if (isYearlyData) {
                return { ...item, date: date.getFullYear().toString() };
            } else if (isMonthlyData) {
                return { ...item, date: date.toLocaleDateString('en-US', { month: 'short' }) };
            } else {
                const month = date.getMonth() + 1;
                const day = date.getDate();
                return { ...item, date: `${month}/${day}` };
            }
        });
    };

    useEffect(() => {
        loadData();
    }, [dateFilters]);

    useEffect(() => {
        if (selectedCustomer && customers.length > 0) {
            const customerData = customers.find(c => c.customer === selectedCustomer);
            setSelectedCustomerData(customerData || null);

            fetchCustomerSpecificData(selectedCustomer);
        }
    }, [selectedCustomer, customers]);

    const loadData = async () => {
        try {
            setLoading(true);

            const filters = {
                start_date: dateFilters.start_date,
                end_date: dateFilters.end_date
            };

            const [
                customerList,
                severityDist,
                trends,
                categories
            ] = await Promise.all([
                fetchTopCustomers(filters),
                fetchSeverityDistribution(filters),
                fetchServiceRequestTrends(filters),
                fetchIssueCategories(filters)
            ]);

            setCustomers(customerList);
            setSeverityData(severityDist);
            setTrendData(trends);

            const formatted = formatTrendDates(trends);
            setFormattedTrends(formatted);

            setIssueCategories(categories);

            if (customerList.length > 0 && !selectedCustomer) {
                setSelectedCustomer(customerList[0].customer);
            }

        } catch (error) {
            console.error("Error loading service performance data:", error);
        } finally {
            setLoading(false);
        }
    };

    const fetchCustomerSpecificData = async (customerName: string) => {
        try {
            const filters = {
                start_date: dateFilters.start_date,
                end_date: dateFilters.end_date,
                customer: customerName
            };

            const [
                metricsData,
                times,
                technicians,
                machineDist
            ] = await Promise.all([
                fetchServiceMetrics(filters),
                fetchTimeAnalysis(filters),
                fetchTechnicianPerformance(filters),
                fetchServiceMachineDistribution(filters)
            ]);

            setMetrics(metricsData);
            setTimeAnalysis(times);
            setTechnicianPerformance(technicians);
            setMachineDistribution(machineDist);

        } catch (error) {
            console.error(`Error loading data for customer ${customerName}:`, error);
        }
    };

    const handleCustomerChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
        const newCustomer = e.target.value;
        setSelectedCustomer(newCustomer);
    };

    const getStatCardData = () => {

        const customerRequests = selectedCustomerData ? selectedCustomerData.serviceRequests : 'N/A';
        const customerPercent = selectedCustomerData ? selectedCustomerData.percentTotal : 'N/A';
        const customerResolution = selectedCustomerData ? selectedCustomerData.avgResolutionTime : 'N/A';


        const travelTimeFormatted = metrics?.travel_time?.formatted || "0h 0m";
        const serviceTimeFormatted = metrics?.service_time?.formatted || "0h 0m";

        const efficiency = timeAnalysis?.overview ?
            ((timeAnalysis.overview.serviceTime || 0) / Math.max(timeAnalysis.overview.totalTime || 1, 1) * 100).toFixed(1) :
            "0.0";


        const activeTechnicians = technicianPerformance?.length || 0;

        return [
            {
                icon: <FiPhoneCall color="#FF6900" size={24} />,
                label: "Service Request Volume",
                value: `${customerRequests} SRs`,
                trend: `${customerPercent} of total requests`,
                trendType: "positive"
            },
            {
                icon: <FiClock color="#FF6900" size={24} />,
                label: "Avg. Resolution Time",
                value: customerResolution,
                trend: "for this customer",
                trendType: "neutral"
            },
            {
                icon: <FiTool color="#FF6900" size={24} />,
                label: "Avg. Task Travel Time",
                value: travelTimeFormatted,
                trend: "per service request",
                trendType: "neutral"
            },
            {
                icon: <FiTrendingUp color="#FF6900" size={24} />,
                label: "Avg. Service Time",
                value: serviceTimeFormatted,
                trend: "per service request",
                trendType: "neutral"
            },
            {
                icon: <FiHardDrive color="#FF6900" size={24} />,
                label: "Active Technicians",
                value: activeTechnicians.toString(),
                trend: "assigned to this customer",
                trendType: "positive"
            },
            {
                icon: <FiSettings color="#FF6900" size={24} />,
                label: "Service Efficiency",
                value: `${efficiency}%`,
                trend: "of time spent on service",
                trendType: "neutral"
            }
        ];
    };

    const formatSeverityData = () => {
        if (severityData.length === 0) {
            return [
                { label: "Critical", count: 0, color: "#F87171" },
                { label: "High", count: 0, color: "#FDBA74" },
                { label: "Medium", count: 0, color: "#FACC15" },
                { label: "Low", count: 0, color: "#4ADE80" },
            ];
        }

        return severityData.map(item => ({
            label: item.label,
            count: item.count,
            color: item.color
        }));
    };

    const formatMachineDistribution = () => {
        if (machineDistribution.length === 0) {
            return [
                { name: "No Data", value: 100, color: "#FF681F" }
            ];
        }

        return machineDistribution.map((item, index) => ({
            name: item.name,
            value: item.percentage,
            count: item.value,
            color: item.color
        }));
    };

    const formatMachineTimeData = (timeType: 'serviceTime' | 'travelTime', color: string) => {
        if (!timeAnalysis?.byMachineType || timeAnalysis.byMachineType.length === 0) {
            return [{ label: "No Data", count: 0, color: color, displayValue: "0h 0m" }];
        }

        return timeAnalysis.byMachineType.map(m => {
            const timeValue = timeType === 'serviceTime' ? (m.serviceTime || 0) : (m.travelTime || 0);
            const formattedTime = formatTime(timeValue);

            return {
                label: m.machineType,
                count: timeValue,
                displayValue: formattedTime,
                color: color
            };
        });
    };

    if (loading && !metrics) {
        return <div className='service-outer-container'>Loading service performance data...</div>;
    }

    return (
        <div className='service-outer-container'>
            <div className='service-insight-container'>
                <div className='service-header'>
                    <h2><b>Key Insights for {selectedCustomer}</b></h2>
                    <div className='customer-dropdown-wrapper'>
                        <select
                            className='customer-dropdown'
                            value={selectedCustomer}
                            onChange={handleCustomerChange}
                        >
                            {customers.map((customer) => (
                                <option key={customer.customer} value={customer.customer}>
                                    {customer.customer}
                                </option>
                            ))}
                        </select>
                    </div>
                </div>
                <div className='service-insight-tab'>
                    {getStatCardData().map((card, index) => (
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

            <div className='service-machine-container'>
                <h2><b>Machine Overview for {selectedCustomer}</b></h2>
                <div className='service-machine-charts'>
                    <div className="chart-box">
                        <h4>Service Requests by Severity</h4>
                        <CustomBarChart data={formatSeverityData()} />
                    </div>
                    <div className="chart-box">
                        <h4>Service Requests Trend</h4>
                        <CustomLineChart
                            data={formattedTrends.length > 0 ? formattedTrends : []}
                            YAxislabel="Service Requests"
                        />
                    </div>
                    <div className="chart-box">
                        <h4>Issues by Category</h4>
                        <ReverseBarChart data={issueCategories.length > 0 ? issueCategories : [
                            { category: 'Touch Screen Failure', value: 25 },
                            { category: 'Scanner Problems', value: 27 },
                            { category: 'Printer Issues', value: 35 },
                            { category: 'Power Problems', value: 45 },
                            { category: 'Software Errors', value: 52 },
                            { category: 'Network Connectivity', value: 58 },
                            { category: 'Hardware Damage', value: 75 },
                            { category: 'RFID Reader Issues', value: 78 },
                        ]} />
                    </div>
                    <div className="chart-box">
                        <h4>Service Time by Machine Type</h4>
                        <p style={{ fontSize: '12px', color: '#666', marginBottom: '10px' }}>
                            {timeAnalysis?.byMachineType ?
                                timeAnalysis.byMachineType.map(m =>
                                    `${m.machineType}: ${formatTime(m.serviceTime || 0)}`
                                ).join(' | ') :
                                'No data available'
                            }
                        </p>
                        <CustomBarChart data={formatMachineTimeData('serviceTime', '#4ADE80')} />
                    </div>
                    <div className="chart-box">
                        <h4>Machine Types Distribution</h4>
                        <CustomPieChart data={formatMachineDistribution()} dollorValue={false} />
                    </div>
                    <div className="chart-box">
                        <h4>Travel Time by Machine Type</h4>
                        <p style={{ fontSize: '12px', color: '#666', marginBottom: '10px' }}>
                            {timeAnalysis?.byMachineType ?
                                timeAnalysis.byMachineType.map(m =>
                                    `${m.machineType}: ${formatTime(m.travelTime || 0)}`
                                ).join(' | ') :
                                'No data available'
                            }
                        </p>
                        <CustomBarChart data={formatMachineTimeData('travelTime', '#FF6900')} />
                    </div>
                </div>
            </div>
        </div>
    );
};

export default ServicePerformance;