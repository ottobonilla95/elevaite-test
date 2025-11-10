'use client';
import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { FiUsers, FiMessageSquare, FiClock, FiTrendingUp, FiDownload, FiBarChart2, FiRefreshCw, FiThumbsUp, FiThumbsDown, FiAlertCircle, FiCheckCircle, FiDatabase, FiUserCheck } from 'react-icons/fi';
import './QueryAnalytics.scss';
import QueryTypeHeatmap from '../SubComponents/QueryTypeHeatmap';

interface DateFilters {
    startDate: string;
    endDate: string;
}

interface ManagerFilter {
    managerId: number | null;
    managerName: string;
}

interface FSTFilter {
    fstId: number | null;
    fstName: string;
}

interface QueryAnalyticsProps {
    dateFilters?: DateFilters;
    managerFilter?: ManagerFilter;
    fstFilter?: FSTFilter;
}

interface FeedbackItem {
    type: string;
    count: number;
    percentage: number;
}

interface QueryMetrics {
    total_sessions: number;
    total_queries: number;
    total_unique_users: number;
    queries_per_session: number;
    repeat_queries_percentage: number;
    accuracy_percentage: number;
    voter_satisfaction_rate: number;
    engagement_rate: number;
    avg_response_time_seconds: number;
    avg_queries_per_day: number;
    avg_unique_users_per_day: number;
    thumbs_up_percentage: number;
    thumbs_down_percentage: number;
    no_vote_percentage: number;
    feedback_distribution: FeedbackItem[];
    _source: string;
    _calculation_method?: string;
    _debug?: {
        total_voted: number;
        thumbs_up_count: number;
        thumbs_down_count: number;
        exact_repeats: number;
        sessions_with_repeats: number;
        total_analyzed: number;
        method1_percentages: string;
        method2_percentages: string;
        total_unique_users: number;
        avg_unique_users_per_day: number;
    };
}

interface HourlyUsageData {
    hour: string;
    queries: number;
}

interface TrendData {
    date: string;
    value: number;
}

interface UnresolvedQuery {
    text: string;
    count: number;
    percentage: string;
    feedback: string;
    botConfidence: string;
    thumbs_up_count: number;
    thumbs_down_count: number;
}

interface ModalQueryData {
    query: string;
    response: string;
    timestamp: string;
    user: string;
    feedback: string;
    session_id: string;
}

interface DateRangeInfo {
    available_range: {
        start_date: string;
        end_date: string;
        total_records: number;
    };
    filtered_range: {
        start_date: string;
        end_date: string;
        total_records: number;
    };
    has_data_in_range: boolean;
}

const QueryAnalyticsDashboard: React.FC<QueryAnalyticsProps> = ({
    dateFilters,
    managerFilter,
    fstFilter
}) => {
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [connectionStatus, setConnectionStatus] = useState<'unknown' | 'connected' | 'error'>('unknown');

    const [metrics, setMetrics] = useState<QueryMetrics>({
        total_sessions: 0,
        total_queries: 0,
        total_unique_users: 0,
        queries_per_session: 0,
        repeat_queries_percentage: 0,
        accuracy_percentage: 0,
        voter_satisfaction_rate: 0,
        engagement_rate: 0,
        avg_response_time_seconds: 0,
        avg_queries_per_day: 0,
        avg_unique_users_per_day: 0,
        thumbs_up_percentage: 0,
        thumbs_down_percentage: 0,
        no_vote_percentage: 0,
        feedback_distribution: [],
        _source: "loading"
    });

    const [hourlyUsageData, setHourlyUsageData] = useState<HourlyUsageData[]>([]);
    const [dailyQueriesData, setDailyQueriesData] = useState<TrendData[]>([]);
    const [dailyUniqueUsersData, setDailyUniqueUsersData] = useState<TrendData[]>([]);
    const [unresolvedQueries, setUnresolvedQueries] = useState<UnresolvedQuery[]>([]);
    const [modalOpen, setModalOpen] = useState(false);
    const [modalType, setModalType] = useState('');
    const [modalData, setModalData] = useState<ModalQueryData[]>([]);
    const [modalLoading, setModalLoading] = useState(false);

    const [dateRangeInfo, setDateRangeInfo] = useState<DateRangeInfo | null>(null);
    const [showDateBanner, setShowDateBanner] = useState(false);

    const [currentPage, setCurrentPage] = useState(1);
    const [itemsPerPage] = useState(6);

    const [showDateRangeModal, setShowDateRangeModal] = useState(false);
    const [dateRangeMessage, setDateRangeMessage] = useState('');

    const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

    const getFeedbackIcon = (feedback: string): string => {
        if (!feedback) return 'No feedback';

        const lowerFeedback = feedback.toLowerCase();

        if (lowerFeedback.includes('positive')) {
            return '👍';
        }

        if (lowerFeedback.includes('negative')) {
            return '👎';
        }

        return feedback;
    };

    const getExportType = (modalType: string): 'thumbs-up' | 'thumbs-down' | 'no-feedback' => {
        console.log('Mapping modal type to export type:', modalType);

        if (modalType === 'user_dissatisfaction' || modalType === 'thumbs_down') {
            console.log('Returning thumbs-down export type');
            return 'thumbs-down';
        }
        if (modalType === 'user_satisfaction' || modalType === 'thumbs_up') {
            console.log('Returning thumbs-up export type');
            return 'thumbs-up';
        }
        if (modalType === 'no_feedback') {
            console.log('Returning no-feedback export type');
            return 'no-feedback';
        }

        console.warn('Unknown modal type, defaulting to thumbs-up:', modalType);
        return 'thumbs-up';
    };

    const totalPages = Math.ceil(unresolvedQueries.length / itemsPerPage);
    const startIndex = (currentPage - 1) * itemsPerPage;
    const endIndex = startIndex + itemsPerPage;
    const currentQueries = unresolvedQueries.slice(startIndex, endIndex);
    const showingStart = startIndex + 1;
    const showingEnd = Math.min(endIndex, unresolvedQueries.length);

    const goToPage = (page: number) => {
        setCurrentPage(page);
    };

    const goToPrevious = () => {
        if (currentPage > 1) {
            setCurrentPage(currentPage - 1);
        }
    };

    const goToNext = () => {
        if (currentPage < totalPages) {
            setCurrentPage(currentPage + 1);
        }
    };

    useEffect(() => {
        loadRealData();
    }, [dateFilters, managerFilter?.managerId, fstFilter?.fstId]);

    useEffect(() => {
        setCurrentPage(1);
    }, [unresolvedQueries]);

    const loadRealData = async () => {
        try {
            setLoading(true);
            setError(null);
            console.log('🔄 Loading real query analytics data with filters:', { dateFilters, managerFilter, fstFilter });

            await testConnection();

            const filters = {
                start_date: dateFilters?.startDate,
                end_date: dateFilters?.endDate,
                manager_id: managerFilter?.managerId || undefined,
                fst_id: fstFilter?.fstId || undefined
            };

            await Promise.all([
                loadDateRangeInfo(filters),
                loadMetrics(filters),
                loadHourlyUsage(filters),
                loadDailyQueries(filters),
                loadDailyUniqueUsers(filters),
                loadUnresolvedQueries(filters)
            ]);

        } catch (error) {
            console.error('Error loading real query analytics data:', error);
            setError(error instanceof Error ? error.message : 'Failed to load data');
            setConnectionStatus('error');
            if (error instanceof Error && error.message.includes('Failed to fetch')) {
                loadFallbackData();
            }
        } finally {
            setLoading(false);
        }
    };

    const testConnection = async () => {
        try {
            const response = await fetch(`${API_URL}/api/analytics/query-analytics/test-connection`);
            const result = await response.json();

            if (result.status === 'success') {
                setConnectionStatus('connected');
                console.log(' Connected to chatbot database:', result.total_queries, 'total queries');
            } else {
                setConnectionStatus('error');
                console.warn(' Connection test failed:', result.message);
            }
        } catch (error) {
            setConnectionStatus('error');
            console.error(' Connection test error:', error);
            throw error;
        }
    };

    const loadDateRangeInfo = async (filters: any) => {
        try {
            const params = new URLSearchParams();
            if (filters?.start_date) params.append('start_date', filters.start_date);
            if (filters?.end_date) params.append('end_date', filters.end_date);
            if (filters?.manager_id) params.append('manager_id', filters.manager_id.toString());
            if (filters?.fst_id) params.append('fst_id', filters.fst_id.toString());

            const queryString = params.toString() ? `?${params.toString()}` : '';
            const response = await fetch(`${API_URL}/api/analytics/query-analytics/date-range-info${queryString}`);

            if (response.ok) {
                const info = await response.json();
                setDateRangeInfo(info);
                setShowDateBanner(true);
                console.log(' Date range info:', info);
            }
        } catch (error) {
            console.error('Error loading date range info:', error);
        }
    };

    const loadMetrics = async (filters: any) => {
        try {
            const params = new URLSearchParams();
            if (filters?.start_date) params.append('start_date', filters.start_date);
            if (filters?.end_date) params.append('end_date', filters.end_date);
            if (filters?.manager_id) params.append('manager_id', filters.manager_id.toString());
            if (filters?.fst_id) params.append('fst_id', filters.fst_id.toString());

            const queryString = params.toString() ? `?${params.toString()}` : '';
            const response = await fetch(`${API_URL}/api/analytics/query-analytics/metrics${queryString}`);

            if (response.ok) {
                const realMetrics = await response.json();
                console.log('Real metrics loaded:', realMetrics);
                setMetrics(realMetrics);
            } else {
                throw new Error(`Metrics API failed: ${response.status} ${response.statusText}`);
            }
        } catch (error) {
            console.error('Error loading metrics:', error);
            throw error;
        }
    };

    const loadHourlyUsage = async (filters: any) => {
        try {
            const params = new URLSearchParams();
            if (filters?.start_date) params.append('start_date', filters.start_date);
            if (filters?.end_date) params.append('end_date', filters.end_date);
            if (filters?.manager_id) params.append('manager_id', filters.manager_id.toString());
            if (filters?.fst_id) params.append('fst_id', filters.fst_id.toString());

            const queryString = params.toString() ? `?${params.toString()}` : '';
            const response = await fetch(`${API_URL}/api/analytics/query-analytics/hourly-usage${queryString}`);

            if (response.ok) {
                const realHourlyData = await response.json();
                console.log('⏰ Real hourly usage loaded:', realHourlyData.length, 'data points');
                setHourlyUsageData(realHourlyData);
            } else {
                console.warn('Hourly usage API failed, using empty data');
                setHourlyUsageData([]);
            }
        } catch (error) {
            console.error('Error loading hourly usage:', error);
            setHourlyUsageData([]);
        }
    };

    const loadDailyQueries = async (filters: any) => {
        try {
            const params = new URLSearchParams();
            if (filters?.start_date) params.append('start_date', filters.start_date);
            if (filters?.end_date) params.append('end_date', filters.end_date);
            if (filters?.manager_id) params.append('manager_id', filters.manager_id.toString());
            if (filters?.fst_id) params.append('fst_id', filters.fst_id.toString());

            const queryString = params.toString() ? `?${params.toString()}` : '';
            const response = await fetch(`${API_URL}/api/analytics/query-analytics/daily-trends${queryString}`);

            if (response.ok) {
                const dailyData = await response.json();
                console.log(' Daily queries loaded:', dailyData.length, 'data points');
                setDailyQueriesData(dailyData);
            } else {
                console.warn('Daily queries API failed');
                setDailyQueriesData([]);
            }
        } catch (error) {
            console.error('Error loading daily queries:', error);
            setDailyQueriesData([]);
        }
    };

    const loadDailyUniqueUsers = async (filters: any) => {
        try {
            const params = new URLSearchParams();
            if (filters?.start_date) params.append('start_date', filters.start_date);
            if (filters?.end_date) params.append('end_date', filters.end_date);
            if (filters?.manager_id) params.append('manager_id', filters.manager_id.toString());
            if (filters?.fst_id) params.append('fst_id', filters.fst_id.toString());

            const queryString = params.toString() ? `?${params.toString()}` : '';
            const response = await fetch(`${API_URL}/api/analytics/query-analytics/daily-unique-users${queryString}`);

            if (response.ok) {
                const dailyUsersData = await response.json();
                console.log(' Daily unique users loaded:', dailyUsersData.length, 'data points');
                setDailyUniqueUsersData(dailyUsersData);
            } else {
                console.warn('Daily unique users API failed');
                setDailyUniqueUsersData([]);
            }
        } catch (error) {
            console.error('Error loading daily unique users:', error);
            setDailyUniqueUsersData([]);
        }
    };

    const loadUnresolvedQueries = async (filters: any) => {
        try {
            const params = new URLSearchParams();
            if (filters?.start_date) params.append('start_date', filters.start_date);
            if (filters?.end_date) params.append('end_date', filters.end_date);
            if (filters?.manager_id) params.append('manager_id', filters.manager_id.toString());
            if (filters?.fst_id) params.append('fst_id', filters.fst_id.toString());
            params.append('limit', '100');

            const queryString = `?${params.toString()}`;
            const response = await fetch(`${API_URL}/api/analytics/query-analytics/unresolved-queries${queryString}`);

            if (response.ok) {
                const realUnresolvedData = await response.json();
                console.log(' Real unresolved queries loaded:', realUnresolvedData.length, 'queries');
                setUnresolvedQueries(realUnresolvedData);
            } else {
                console.warn('Unresolved queries API failed');
                setUnresolvedQueries([]);
            }
        } catch (error) {
            console.error('Error loading unresolved queries:', error);
            setUnresolvedQueries([]);
        }
    };

    const loadFallbackData = () => {
        console.warn('Loading fallback data - Backend unavailable');
        setMetrics({
            total_sessions: 24600,
            total_queries: 30200,
            total_unique_users: 18500,
            queries_per_session: 1.23,
            repeat_queries_percentage: 23.4,
            accuracy_percentage: 62.2,
            voter_satisfaction_rate: 62.2,
            engagement_rate: 11.9,
            avg_response_time_seconds: 2.3,
            avg_queries_per_day: 1007,
            avg_unique_users_per_day: 617,
            thumbs_up_percentage: 7.4,
            thumbs_down_percentage: 4.5,
            no_vote_percentage: 88.1,
            feedback_distribution: [],
            _source: "fallback_data",
            _debug: {
                thumbs_up_count: 325,
                thumbs_down_count: 157,
                total_voted: 482,
                sessions_with_repeats: 834,
                exact_repeats: 1247,
                total_analyzed: 30200,
                method1_percentages: '',
                method2_percentages: '',
                total_unique_users: 0,
                avg_unique_users_per_day: 0
            }
        });

        setHourlyUsageData([
            { hour: '00:00', queries: 45 }, { hour: '01:00', queries: 32 }, { hour: '02:00', queries: 28 }, { hour: '03:00', queries: 25 },
            { hour: '04:00', queries: 30 }, { hour: '05:00', queries: 45 }, { hour: '06:00', queries: 78 }, { hour: '07:00', queries: 120 },
            { hour: '08:00', queries: 180 }, { hour: '09:00', queries: 220 }, { hour: '10:00', queries: 250 }, { hour: '11:00', queries: 280 },
            { hour: '12:00', queries: 265 }, { hour: '13:00', queries: 240 }, { hour: '14:00', queries: 235 }, { hour: '15:00', queries: 210 },
            { hour: '16:00', queries: 195 }, { hour: '17:00', queries: 165 }, { hour: '18:00', queries: 140 }, { hour: '19:00', queries: 110 },
            { hour: '20:00', queries: 85 }, { hour: '21:00', queries: 70 }, { hour: '22:00', queries: 60 }, { hour: '23:00', queries: 50 }
        ]);

        setDailyQueriesData([
            { date: '01/01', value: 980 }, { date: '01/02', value: 1050 }, { date: '01/03', value: 890 }, { date: '01/04', value: 1120 },
            { date: '01/05', value: 1340 }, { date: '01/06', value: 1290 }, { date: '01/07', value: 945 }, { date: '01/08', value: 1150 },
            { date: '01/09', value: 1230 }, { date: '01/10', value: 1080 }, { date: '01/11', value: 1190 }, { date: '01/12', value: 1320 }
        ]);

        setDailyUniqueUsersData([
            { date: '01/01', value: 580 }, { date: '01/02', value: 640 }, { date: '01/03', value: 520 }, { date: '01/04', value: 690 },
            { date: '01/05', value: 780 }, { date: '01/06', value: 750 }, { date: '01/07', value: 560 }, { date: '01/08', value: 680 },
            { date: '01/09', value: 720 }, { date: '01/10', value: 630 }, { date: '01/11', value: 710 }, { date: '01/12', value: 800 }
        ]);

        setUnresolvedQueries([
            { text: "How do I reset the X4000 model after error code E72?", count: 1247, percentage: "4.1%", feedback: "Mostly 👎", botConfidence: "42%", thumbs_up_count: 12, thumbs_down_count: 45 },
            { text: "What does error code E72 mean on 335 series?", count: 986, percentage: "3.3%", feedback: "Mostly 👎", botConfidence: "38%", thumbs_up_count: 8, thumbs_down_count: 52 }
        ]);
    };

    const handleExport = async (exportType: 'all-queries' | 'thumbs-up' | 'thumbs-down' | 'no-feedback') => {
        try {
            console.log(`Starting export: ${exportType}`);

            const params = new URLSearchParams();
            if (dateFilters?.startDate) params.append('start_date', dateFilters.startDate);
            if (dateFilters?.endDate) params.append('end_date', dateFilters.endDate);
            if (managerFilter?.managerId) params.append('manager_id', managerFilter.managerId.toString());
            if (fstFilter?.fstId) params.append('fst_id', fstFilter.fstId.toString());

            const queryString = params.toString() ? `?${params.toString()}` : '';

            const endpointMap = {
                'all-queries': '/export/all-queries',
                'thumbs-up': '/export/thumbs-up',
                'thumbs-down': '/export/thumbs-down',
                'no-feedback': '/export/no-feedback'
            };

            const endpoint = endpointMap[exportType];
            const url = `${API_URL}/api/analytics/query-analytics${endpoint}${queryString}`;

            console.log(`Fetching export response: ${url}`);
            console.log('Final URL being called:', url);

            const response = await fetch(url);
            const contentType = response.headers.get('Content-Type') || '';

            if (contentType.includes('application/json')) {
                const errorData = await response.json();
                if (errorData.error === 'date_range_required') {
                    setDateRangeMessage(errorData.message || 'Please select a date range to export data.');
                    setShowDateRangeModal(true);
                    return;
                } else {
                    throw new Error(errorData.message || 'Export failed');
                }
            } else if (contentType.includes('spreadsheet') || contentType.includes('excel')) {
                console.log(`Starting Excel download: ${url}`);
                window.open(url, '_blank');
                console.log(`Export initiated: ${exportType}`);
            } else {
                throw new Error('Unexpected response format');
            }

        } catch (error) {
            console.error(`Export failed:`, error);
            setError('Export failed. Please try again.');
        }
    };

    const openModal = async (type: string) => {
        try {
            setModalType(type);
            setModalOpen(true);
            setModalLoading(true);

            const filters = {
                start_date: dateFilters?.startDate,
                end_date: dateFilters?.endDate,
                manager_id: managerFilter?.managerId || undefined,
                fst_id: fstFilter?.fstId || undefined
            };

            if (type === 'thumbs_up' || type === 'thumbs_down' || type === 'user_satisfaction' || type === 'user_dissatisfaction' || type === 'no_feedback') {
                let feedbackType;

                if (type === 'user_satisfaction' || type === 'thumbs_up') {
                    feedbackType = 'thumbs_up';
                } else if (type === 'user_dissatisfaction' || type === 'thumbs_down') {
                    feedbackType = 'thumbs_down';
                } else if (type === 'no_feedback') {
                    feedbackType = 'no_feedback';
                }

                const params = new URLSearchParams();
                if (filters.start_date) params.append('start_date', filters.start_date);
                if (filters.end_date) params.append('end_date', filters.end_date);
                if (filters.manager_id) params.append('manager_id', filters.manager_id.toString());
                if (filters.fst_id) params.append('fst_id', filters.fst_id.toString());
                params.append('feedback_type', feedbackType);
                params.append('limit', '10');

                const queryString = `?${params.toString()}`;
                const response = await fetch(`${API_URL}/api/analytics/query-analytics/feedback-queries${queryString}`);

                if (response.ok) {
                    const data = await response.json();
                    setModalData(data);
                    console.log(`Modal data loaded for ${type}:`, data.length, 'queries');
                } else {
                    setModalData([]);
                    console.warn(`Modal data loading failed for ${type}`);
                }
            }
        } catch (error) {
            console.error('Error loading modal data:', error);
            setModalData([]);
        } finally {
            setModalLoading(false);
        }
    };

    const closeModal = () => {
        setModalOpen(false);
        setModalType('');
        setModalData([]);
        setModalLoading(false);
    };

    const renderDateBanner = () => {
        if (!showDateBanner || !dateRangeInfo) return null;

        const { available_range, filtered_range, has_data_in_range } = dateRangeInfo;

        let bannerType: 'info' | 'warning' | 'error' = 'info';
        let icon = <FiCheckCircle />;
        let message = '';
        let details = '';

        if (!has_data_in_range) {
            bannerType = 'warning';
            icon = <FiAlertCircle />;
            message = 'No query data in selected date range';
            details = `Available data: ${available_range.start_date} to ${available_range.end_date} (${available_range.total_records?.toLocaleString()} queries)`;
        } else if (dateFilters?.startDate || dateFilters?.endDate) {
            message = 'Showing filtered query data';
            details = `${filtered_range.total_records?.toLocaleString()} queries from ${filtered_range.start_date} to ${filtered_range.end_date}`;
        } else {
            message = 'Showing all available query data';
            details = `${available_range.total_records?.toLocaleString()} queries from ${available_range.start_date} to ${available_range.end_date}`;
        }

        return (
            <div className={`date-range-banner ${bannerType}`}>
                <div className="banner-content">
                    <div className="banner-icon">{icon}</div>
                    <div className="banner-text">
                        <div className="banner-message">{message}</div>
                        <div className="banner-details">{details}</div>
                    </div>
                </div>
            </div>
        );
    };

    if (loading) {
        return (
            <div className="query-analytics">
                <div className="loading-container">
                    <div className="loading-spinner"></div>
                    <p>Loading query analytics...</p>
                </div>
            </div>
        );
    }

    if (error && connectionStatus === 'error' && metrics._source === "loading") {
        return (
            <div className="query-analytics">
                <div className="error-container">
                    <FiAlertCircle size={48} />
                    <h3>Connection Error</h3>
                    <p>{error}</p>
                    <button onClick={loadRealData} className="retry-btn">
                        <FiRefreshCw /> Try Again
                    </button>
                </div>
            </div>
        );
    }

    const summaryCards = [
        {
            name: "Total Sessions",
            value: metrics.total_sessions?.toLocaleString() || "0",
            icon: <FiUsers />,
            desc: "Unique user sessions",
            trend: ""
        },
        {
            name: "Total Queries",
            value: metrics.total_queries?.toLocaleString() || "0",
            icon: <FiMessageSquare />,
            desc: "Questions asked by users",
            trend: ""
        },
        {
            name: "Unique Users",
            value: metrics.total_unique_users?.toLocaleString() || "0",
            icon: <FiUserCheck />,
            desc: "Distinct users served",
            trend: ""
        },
        {
            name: "Avg Queries/Day",
            value: Math.round(metrics.avg_queries_per_day || 0).toLocaleString(),
            icon: <FiBarChart2 />,
            desc: "Daily query volume",
            trend: `${Math.round(metrics.avg_queries_per_day / 24 || 0)} per hour`
        },
        {
            name: "Avg Users/Day",
            value: Math.round(metrics.avg_unique_users_per_day || 0).toLocaleString(),
            icon: <FiUsers />,
            desc: "Daily unique users",
            trend: ""
        },
        {
            name: "Response Time",
            value: `${metrics.avg_response_time_seconds?.toFixed(1) || '0.0'}s`,
            icon: <FiClock />,
            desc: "Average response time",
            trend: ""
        }
    ];

    const statCards = [
        {
            icon: <FiThumbsUp />,
            title: "User Satisfaction",
            value: `${(metrics.voter_satisfaction_rate || 0).toFixed(1)}%`,
            desc: "Among users who voted",
            trend: `${metrics._debug?.thumbs_up_count || 0} positive votes`
        },
        {
            icon: <FiRefreshCw />,
            title: "Repeat Queries",
            value: `${(metrics.repeat_queries_percentage || 0).toFixed(1)}%`,
            desc: "Users asking similar questions",
            trend: `${metrics._debug?.sessions_with_repeats || 0} sessions affected`
        },
        {
            icon: <FiClock />,
            title: "Avg Response Time",
            value: `${(metrics.avg_response_time_seconds || 0).toFixed(1)}s`,
            desc: "Time to generate response",
            trend: ""
        },
        {
            icon: <FiTrendingUp />,
            title: "Engagement Rate",
            value: `${(metrics.engagement_rate || 0).toFixed(1)}%`,
            desc: "Users who provided feedback",
            trend: `${metrics._debug?.total_voted || 0} total votes`
        }
    ];

    const feedbackCards = [
        {
            name: "User Satisfaction",
            value: `${metrics.thumbs_up_percentage?.toFixed(1) || '0.0'}%`,
            icon: <FiThumbsUp />,
            desc: `${metrics._debug?.thumbs_up_count?.toLocaleString() || '0'} thumbs up`,
            trend: "Positive feedback",
            color: "#10B981",
            onClick: () => openModal('user_satisfaction')
        },
        {
            name: "User Dissatisfaction",
            value: `${metrics.thumbs_down_percentage?.toFixed(1) || '0.0'}%`,
            icon: <FiThumbsDown />,
            desc: `${metrics._debug?.thumbs_down_count?.toLocaleString() || '0'} thumbs down`,
            trend: "Negative feedback",
            color: "#EF4444",
            onClick: () => openModal('user_dissatisfaction')
        },
        {
            name: "No Feedback",
            value: `${metrics.no_vote_percentage?.toFixed(1) || '0.0'}%`,
            icon: <FiDatabase />,
            desc: "Queries without votes",
            trend: "Neutral responses",
            color: "#6B7280",
            onClick: () => openModal('no_feedback')
        },
        {
            name: "Engagement Rate",
            value: `${metrics.engagement_rate?.toFixed(1) || '0.0'}%`,
            icon: <FiTrendingUp />,
            desc: "Users who voted",
            trend: `${metrics._debug?.total_voted?.toLocaleString() || '0'} total votes`,
            color: "#3B82F6"
        }
    ];

    return (
        <div className="query-analytics">
            {renderDateBanner()}

            {/* FST Filter Display */}
            {/* {(managerFilter?.managerId || fstFilter?.fstId) && (
                <div style={{
                    background: '#e3f2fd',
                    padding: '8px 16px',
                    marginBottom: '16px',
                    borderLeft: '4px solid #1976d2',
                    fontSize: '14px',
                    color: '#1976d2',
                    borderRadius: '0 4px 4px 0'
                }}>
                    {managerFilter?.managerId && !fstFilter?.fstId && (
                        <span> Manager Filter: {managerFilter.managerName}</span>
                    )}
                    {fstFilter?.fstId && (
                        <span> FST Filter: {fstFilter.fstName}</span>
                    )}
                </div>
            )} */}

            <div className="summary-section">
                <div className="section-header">
                    <h2>Query Analytics Summary</h2>
                    <div className="export-header">
                        {/* <button
                            onClick={() => handleExport('all-queries')}
                            className="export-btn"
                        >
                            <FiDownload /> Export All Data
                        </button> */}
                    </div>
                </div>

                <div className="cards-grid-six">
                    {summaryCards.map((card, index) => (
                        <div key={index} className="summary-card">
                            <div className="card-header">
                                <div className="card-icon">{card.icon}</div>
                                <div className="card-title">{card.name}</div>
                            </div>
                            <div className="card-value">{card.value}</div>
                            <div className="card-desc">{card.desc}</div>
                            <div className="card-trend">{card.trend}</div>
                        </div>
                    ))}
                </div>
            </div>

            <div className="analytics-section">
                <div className="section-header">
                    <h2>Query Performance Insights</h2>
                </div>

                <div className="stat-cards-grid">
                    {statCards.map((card, index) => (
                        <div key={index} className="stat-card">
                            <div className="stat-header">
                                <div className="stat-icon">{card.icon}</div>
                                <div className="stat-title">{card.title}</div>
                            </div>
                            <div className="stat-value">{card.value}</div>
                            <div className="stat-desc">{card.desc}</div>
                            <div className="stat-trend">{card.trend}</div>
                        </div>
                    ))}
                </div>
            </div>

            <div className="feedback-section">
                <div className="section-header">
                    <h2>User Feedback & Satisfaction</h2>
                </div>

                <div className="charts-row-side-by-side">
                    <div className="chart-container large">
                        <div className="chart-header">
                            <h3>Query Volume Trend</h3>
                        </div>
                        <div className="chart-body">
                            <ResponsiveContainer width="100%" height="100%">
                                <LineChart data={dailyQueriesData} margin={{ top: 20, right: 30, left: 20, bottom: 60 }}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                                    <XAxis dataKey="date" tick={{ fontSize: 11 }} interval={2} angle={-45} textAnchor="end" height={60} />
                                    <YAxis tick={{ fontSize: 11 }} />
                                    <Tooltip contentStyle={{ backgroundColor: 'white', border: '1px solid #ddd', borderRadius: '8px', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }} />
                                    <Line type="monotone" dataKey="value" stroke="#3B82F6" strokeWidth={3} dot={{ r: 4, fill: "#3B82F6" }} />
                                </LineChart>
                            </ResponsiveContainer>
                        </div>
                    </div>

                    <div className="chart-container medium">
                        <div className="chart-header">
                            <h3>Real User Feedback Distribution</h3>
                            <div className="connection-indicator">
                                {connectionStatus === 'connected' ? (
                                    <div className="connected">
                                        <FiCheckCircle size={12} />
                                        {metrics._source === 'real_chatbot_database' ? 'Real data' : metrics._source === 'fallback_data' ? 'Sample data' : 'Backend data'}
                                    </div>
                                ) : (
                                    <div className="error">
                                        <FiAlertCircle size={12} />
                                        Connection error
                                    </div>
                                )}
                            </div>
                        </div>
                        <div className="chart-body feedback-chart">
                            <div className="donut-section">
                                <ResponsiveContainer width="100%" height="100%">
                                    <PieChart>
                                        <Pie
                                            data={[
                                                { name: 'Thumbs Up', value: metrics.thumbs_up_percentage, color: '#10B981' },
                                                { name: 'Thumbs Down', value: metrics.thumbs_down_percentage, color: '#EF4444' },
                                                { name: 'No Vote', value: metrics.no_vote_percentage, color: '#6B7280' }
                                            ]}
                                            cx="50%"
                                            cy="50%"
                                            innerRadius={40}
                                            outerRadius={80}
                                            dataKey="value"
                                        >
                                            {[
                                                { name: 'Thumbs Up', value: metrics.thumbs_up_percentage, color: '#10B981' },
                                                { name: 'Thumbs Down', value: metrics.thumbs_down_percentage, color: '#EF4444' },
                                                { name: 'No Vote', value: metrics.no_vote_percentage, color: '#6B7280' }
                                            ].map((entry, index) => (
                                                <Cell key={`cell-${index}`} fill={entry.color} />
                                            ))}
                                        </Pie>
                                        <Tooltip formatter={(value) => `${Number(value).toFixed(1)}%`} />
                                    </PieChart>
                                </ResponsiveContainer>
                            </div>
                            <div className="feedback-legend">
                                {[
                                    {
                                        name: ' ',
                                        percentage: metrics.thumbs_up_percentage,
                                        count: metrics._debug?.thumbs_up_count || 0,
                                        color: '#10B981',
                                        icon: 'Thumbs Up',
                                        onClick: () => openModal('user_satisfaction')
                                    },
                                    {
                                        name: ' ',
                                        percentage: metrics.thumbs_down_percentage,
                                        count: metrics._debug?.thumbs_down_count || 0,
                                        color: '#EF4444',
                                        icon: 'Thumbs Down',
                                        onClick: () => openModal('user_dissatisfaction')
                                    },
                                    {
                                        name: ' ',
                                        percentage: metrics.no_vote_percentage,
                                        count: (metrics.total_queries || 0) - (metrics._debug?.total_voted || 0),
                                        color: '#6B7280',
                                        icon: 'No Feedback',
                                        onClick: () => openModal('no_feedback')
                                    }
                                ].map((item, index) => (
                                    <div key={index} className="legend-item">
                                        <div
                                            className="legend-indicator"
                                            style={{ backgroundColor: item.color }}
                                        ></div>
                                        <div className="legend-content">
                                            <div className="legend-title">
                                                {item.icon} {item.name}
                                            </div>
                                            <div className="legend-stats">
                                                <span className="count">{item.count?.toLocaleString() || '0'} queries</span>
                                                <span className="percentage">{item.percentage?.toFixed(1) || '0.0'}%</span>
                                            </div>
                                            {item.onClick && (
                                                <button
                                                    onClick={item.onClick}
                                                    className="view-link"
                                                >
                                                    view queries
                                                </button>
                                            )}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                </div>

                <div className="charts-row-side-by-side" style={{ marginTop: '24px' }}>
                    <div className="chart-container large">
                        <div className="chart-header">
                            <h3>24-Hour Usage Pattern</h3>
                        </div>
                        <div className="chart-body">
                            <ResponsiveContainer width="100%" height="100%">
                                <LineChart data={hourlyUsageData} margin={{ top: 20, right: 30, left: 20, bottom: 60 }}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                                    <XAxis dataKey="hour" tick={{ fontSize: 11 }} interval={2} angle={-45} textAnchor="end" height={60} />
                                    <YAxis tick={{ fontSize: 11 }} />
                                    <Tooltip contentStyle={{ backgroundColor: 'white', border: '1px solid #ddd', borderRadius: '8px', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }} />
                                    <Line type="monotone" dataKey="queries" stroke="#FF6600" strokeWidth={3} dot={{ r: 4, fill: "#FF6600" }} />
                                </LineChart>
                            </ResponsiveContainer>
                        </div>
                    </div>

                    <div className="chart-container medium">
                        <div className="chart-header">
                            <h3>Unique Users per Day</h3>
                        </div>
                        <div className="chart-body">
                            <ResponsiveContainer width="100%" height="100%">
                                <LineChart data={dailyUniqueUsersData} margin={{ top: 20, right: 30, left: 20, bottom: 60 }}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                                    <XAxis dataKey="date" tick={{ fontSize: 11 }} interval={2} angle={-45} textAnchor="end" height={60} />
                                    <YAxis tick={{ fontSize: 11 }} />
                                    <Tooltip contentStyle={{ backgroundColor: 'white', border: '1px solid #ddd', borderRadius: '8px', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }} />
                                    <Line type="monotone" dataKey="value" stroke="#10B981" strokeWidth={3} dot={{ r: 4, fill: "#10B981" }} />
                                </LineChart>
                            </ResponsiveContainer>
                        </div>
                    </div>
                </div>
            </div>

            {/* Query Type Heatmap Section */}
            <QueryTypeHeatmap
                dateFilters={dateFilters}
                managerFilter={managerFilter}
                fstFilter={fstFilter}
            />

            <div className="unresolved-section">
                <div className="section-header">
                    <h2>Top Unresolved Queries Analysis</h2>
                </div>

                <div className="table-container">
                    <table className="queries-table">
                        <thead>
                            <tr>
                                <th className="query-column">Query Text</th>
                                <th className="count-column">Count</th>
                                <th className="percent-column">% of Total</th>
                            </tr>
                        </thead>
                        <tbody>
                            {currentQueries.map((query, index) => (
                                <tr key={index}>
                                    <td className="query-text">"{query.text}"</td>
                                    <td className="count-value">{query.count?.toLocaleString() || 0}</td>
                                    <td><span className="percentage-badge">{query.percentage || '0%'}</span></td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>

                <div className="pagination-wrapper">
                    <div className="pagination-info">
                        Showing {unresolvedQueries.length > 0 ? showingStart : 0} to {showingEnd} of {unresolvedQueries.length} unresolved queries
                    </div>

                    {totalPages > 1 && (
                        <div className="pagination-controls">
                            <button
                                onClick={goToPrevious}
                                disabled={currentPage === 1}
                                className="pagination-btn"
                            >
                                Previous
                            </button>

                            <div className="pagination-numbers">
                                {Array.from({ length: Math.min(totalPages, 5) }, (_, i) => {
                                    let pageNumber;
                                    if (totalPages <= 5) {
                                        pageNumber = i + 1;
                                    } else if (currentPage <= 3) {
                                        pageNumber = i + 1;
                                    } else if (currentPage >= totalPages - 2) {
                                        pageNumber = totalPages - 4 + i;
                                    } else {
                                        pageNumber = currentPage - 2 + i;
                                    }

                                    return (
                                        <button
                                            key={pageNumber}
                                            onClick={() => goToPage(pageNumber)}
                                            className={`pagination-number ${currentPage === pageNumber ? 'active' : ''}`}
                                        >
                                            {pageNumber}
                                        </button>
                                    );
                                })}
                            </div>

                            <button
                                onClick={goToNext}
                                disabled={currentPage === totalPages}
                                className="pagination-btn"
                            >
                                Next
                            </button>
                        </div>
                    )}
                </div>
            </div>

            {modalOpen && (
                <div className="modal-overlay" onClick={closeModal}>
                    <div className="modal-content" onClick={(e) => e.stopPropagation()}>
                        <div className="modal-header">
                            <h3>
                                {modalType === 'thumbs_up' ? 'Positive Feedback Queries' :
                                    modalType === 'user_satisfaction' ? 'User Satisfaction Queries' :
                                        modalType === 'thumbs_down' ? 'Negative Feedback Queries' :
                                            modalType === 'user_dissatisfaction' ? 'User Dissatisfaction Queries' :
                                                modalType === 'no_feedback' ? 'No Feedback Queries' :
                                                    'Query Details'}
                                <span className="modal-subtitle">Real database data</span>
                            </h3>
                            <button className="modal-close" onClick={closeModal}>×</button>
                        </div>
                        <div className="modal-body">
                            {modalLoading ? (
                                <div className="modal-loading">
                                    <div className="loading-spinner"></div>
                                    <p>Loading queries...</p>
                                </div>
                            ) : modalData.length > 0 ? (
                                <div className="modal-table-container">
                                    <table className="modal-table">
                                        <thead>
                                            <tr>
                                                <th>Query</th>
                                                <th>User</th>
                                                <th>Timestamp</th>
                                                <th>Feedback</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {modalData.map((item, index) => (
                                                <tr key={index}>
                                                    <td className="query-cell">"{item.query}"</td>
                                                    <td>{item.user}</td>
                                                    <td>{new Date(item.timestamp).toLocaleString()}</td>
                                                    <td>
                                                        <span className={`feedback-badge ${item.feedback === 'thumbs_up' ? 'positive' : item.feedback === 'thumbs_down' ? 'negative' : 'neutral'}`}>
                                                            {item.feedback === 'thumbs_up' ? '👍 Positive' :
                                                                item.feedback === 'thumbs_down' ? '👎 Negative' :
                                                                    item.feedback || 'No feedback'}
                                                        </span>
                                                    </td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            ) : (
                                <div className="no-data-container">
                                    <p>No queries found for this feedback type in the selected date range.</p>
                                </div>
                            )}
                        </div>
                        <div className="modal-footer">
                            <button
                                onClick={() => handleExport(getExportType(modalType))}
                                className="modal-export-btn"
                            >
                                <FiDownload />
                                Export Data
                            </button>
                            <button onClick={closeModal} className="modal-close-btn">
                                Close
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {showDateRangeModal && (
                <div className="modal-overlay" onClick={() => setShowDateRangeModal(false)}>
                    <div className="modal-content" onClick={(e) => e.stopPropagation()}>
                        <div className="modal-header">
                            <h3>📅 Date Range Required</h3>
                            <button className="modal-close" onClick={() => setShowDateRangeModal(false)}>×</button>
                        </div>
                        <div className="modal-body">
                            <p>{dateRangeMessage}</p>
                            <p>Please select a start date and/or end date using the date filters at the top of the page, then try exporting again.</p>
                        </div>
                        <div className="modal-footer">
                            <button onClick={() => setShowDateRangeModal(false)} className="modal-close-btn">
                                OK
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default QueryAnalyticsDashboard;
