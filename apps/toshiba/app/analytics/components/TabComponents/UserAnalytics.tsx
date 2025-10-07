'use client';
import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, BarChart, Bar } from 'recharts';
import {
    FiUsers, FiTrendingUp, FiClock, FiUserCheck, FiActivity, FiDownload,
    FiSearch, FiFilter, FiChevronLeft, FiChevronRight, FiEye, FiRefreshCw,
    FiUserPlus, FiCalendar, FiThumbsUp, FiMessageSquare, FiStar, FiX
} from 'react-icons/fi';
import './UserAnalytics.scss';

interface DateFilters {
    startDate: string;
    endDate: string;
}

interface ManagerFilter {
    id: number;
    name: string;
}

interface FSTFilter {
    id: number;
    full_name: string;
    fst_email: string;
}

interface UserAnalyticsProps {
    dateFilters?: DateFilters;
    managerFilter?: ManagerFilter | null;
    fstFilter?: FSTFilter | null;
}

interface UserMetrics {
    total_unique_users: number;
    avg_queries_per_user: number;
    avg_sessions_per_user: number;
    most_active_user: string;
    newest_user: string;
    user_growth_rate: number;
}

interface TopUser {
    user_id: string;
    total_queries: number;
    total_sessions: number;
    last_active: string;
    avg_queries_per_session: number;
    satisfaction_rate: number;
    thumbs_up_count: number;
    thumbs_down_count: number;
    days_active: number;
}

interface UserBreakdown {
    user_id: string;
    total_queries: number;
    total_sessions: number;
    first_query: string;
    last_active: string;
    avg_queries_per_day: number;
    satisfaction_rate: number;
    most_active_hour: number;
    repeat_query_rate: number;
}

interface UserActivityData {
    date: string;
    users: number;
}

interface FeedbackQueryResponse {
    query: string;
    response: string;
    timestamp: string;
    user: string;
    feedback: string;
    session_id: string;
}

interface RecentQuery {
    query: string;
    response: string;
    timestamp: string;
    vote: number;
    feedback: string;
}

interface UserDetailData {
    user_id: string;
    total_queries: number;
    total_sessions: number;
    first_query: string;
    last_active: string;
    satisfaction_rate: number;
    thumbs_up_count: number;
    thumbs_down_count: number;
    most_active_hour: number;
    repeat_query_rate: number;
    recent_queries: RecentQuery[];
}

const UserAnalyticsDashboard: React.FC<UserAnalyticsProps> = ({
    dateFilters,
    managerFilter,
    fstFilter
}) => {
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    // State for different data sections
    const [userMetrics, setUserMetrics] = useState<UserMetrics>({
        total_unique_users: 0,
        avg_queries_per_user: 0,
        avg_sessions_per_user: 0,
        most_active_user: '',
        newest_user: '',
        user_growth_rate: 0
    });

    const [topUsers, setTopUsers] = useState<TopUser[]>([]);
    const [userBreakdown, setUserBreakdown] = useState<UserBreakdown[]>([]);
    const [userActivityData, setUserActivityData] = useState<UserActivityData[]>([]);

    const [currentPage, setCurrentPage] = useState(1);
    const [itemsPerPage] = useState(20);
    const [searchTerm, setSearchTerm] = useState('');
    const [sortField, setSortField] = useState<keyof UserBreakdown>('total_queries');
    const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('desc');

    const [selectedUser, setSelectedUser] = useState<string | null>(null);
    const [showUserModal, setShowUserModal] = useState(false);
    const [userDetailData, setUserDetailData] = useState<UserDetailData | null>(null);
    const [modalLoading, setModalLoading] = useState(false);

    const [isExporting, setIsExporting] = useState(false);
    const [exportMessage, setExportMessage] = useState('');
    const [exportType, setExportType] = useState<'success' | 'error' | ''>('');

    const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

    useEffect(() => {
        loadUserAnalyticsData();
    }, [dateFilters, managerFilter, fstFilter]);

    const loadUserAnalyticsData = async () => {
        try {
            console.log('UserAnalytics - useEffect triggered with filters:', {
                dateFilters,
                managerFilter,
                fstFilter
            });
            setLoading(true);
            setError(null);
            console.log('UserAnalytics - Starting data load...');

            const filters = {
                start_date: dateFilters?.startDate,
                end_date: dateFilters?.endDate,
                manager_id: managerFilter?.id,
                fst_id: fstFilter?.id
            };

            await loadUserMetrics(filters);
            await loadTopUsers(filters);
            await loadUserBreakdown(filters);
            await loadUserActivity(filters);

            console.log('UserAnalytics - All data loaded successfully');
        } catch (error) {
            console.error('UserAnalytics - Error loading data:', error);
            setError(error instanceof Error ? error.message : 'Failed to load user data');
        } finally {
            console.log('UserAnalytics - Setting loading to false');
            setLoading(false);
        }
    };

    const buildQueryParams = (additionalParams: Record<string, any> = {}) => {
        const params = new URLSearchParams();

        if (dateFilters?.startDate) params.append('start_date', dateFilters.startDate);
        if (dateFilters?.endDate) params.append('end_date', dateFilters.endDate);

        if (managerFilter?.id) params.append('manager_id', managerFilter.id.toString());
        if (fstFilter?.id) params.append('fst_id', fstFilter.id.toString());

        Object.entries(additionalParams).forEach(([key, value]) => {
            if (value !== undefined && value !== null) {
                params.append(key, value.toString());
            }
        });

        return params;
    };

    const loadUserMetrics = async (filters: any) => {
        try {
            console.log('UserAnalytics - Loading user metrics...');
            const params = buildQueryParams();
            const queryString = params.toString() ? `?${params.toString()}` : '';
            const url = `${API_URL}/api/analytics/user-analytics/user-metrics${queryString}`;
            console.log('UserAnalytics - Fetching metrics from:', url);

            const response = await fetch(url);
            if (!response.ok) {
                throw new Error(`Metrics API failed: ${response.status} ${response.statusText}`);
            }

            const data = await response.json();
            setUserMetrics(data);
            console.log('UserAnalytics - User metrics loaded:', data);
        } catch (error) {
            console.error('UserAnalytics - Error loading user metrics:', error);
            throw error;
        }
    };

    const loadTopUsers = async (filters: any) => {
        try {
            console.log('UserAnalytics - Loading top users...');
            const params = buildQueryParams({ limit: '10' });
            const queryString = `?${params.toString()}`;
            const url = `${API_URL}/api/analytics/user-analytics/top-users${queryString}`;
            console.log('UserAnalytics - Fetching top users from:', url);

            const response = await fetch(url);
            if (!response.ok) {
                throw new Error(`Top users API failed: ${response.status} ${response.statusText}`);
            }

            const data = await response.json();
            setTopUsers(data);
            console.log('UserAnalytics - Top users loaded:', data.length, 'users');
        } catch (error) {
            console.error('UserAnalytics - Error loading top users:', error);
            throw error;
        }
    };

    const loadUserBreakdown = async (filters: any) => {
        try {
            console.log('UserAnalytics - Loading user breakdown...');
            const params = buildQueryParams({ page: '1', page_size: '1000' });
            const queryString = `?${params.toString()}`;
            const url = `${API_URL}/api/analytics/user-analytics/user-breakdown${queryString}`;
            console.log('UserAnalytics - Fetching user breakdown from:', url);

            const response = await fetch(url);
            if (!response.ok) {
                throw new Error(`User breakdown API failed: ${response.status} ${response.statusText}`);
            }

            const data = await response.json();
            setUserBreakdown(data);
            console.log('UserAnalytics - User breakdown loaded:', data.length, 'users');
        } catch (error) {
            console.error('UserAnalytics - Error loading user breakdown:', error);
            throw error;
        }
    };

    const loadUserActivity = async (filters: any) => {
        try {
            console.log('UserAnalytics - Loading user activity...');
            const params = buildQueryParams();
            const queryString = params.toString() ? `?${params.toString()}` : '';
            const url = `${API_URL}/api/analytics/user-analytics/daily-unique-users${queryString}`;
            console.log('UserAnalytics - Fetching user activity from:', url);

            const response = await fetch(url);
            if (!response.ok) {
                throw new Error(`User activity API failed: ${response.status} ${response.statusText}`);
            }

            const data = await response.json();
            setUserActivityData(data.map((item: any) => ({
                date: item.date,
                users: item.value
            })));
            console.log('UserAnalytics - User activity loaded:', data.length, 'days');
        } catch (error) {
            console.error('UserAnalytics - Error loading user activity:', error);
            throw error;
        }
    };

    const loadUserDetails = async (userId: string) => {
        try {
            setModalLoading(true);
            console.log('UserAnalytics - Loading details for user:', userId);

            const userInfo = userBreakdown.find(u => u.user_id === userId);

            if (!userInfo) {
                console.error('UserAnalytics - User not found in breakdown data:', userId);
                return;
            }

            let recentQueries: RecentQuery[] = [];

            try {
                console.log('UserAnalytics - Fetching recent chat sessions for user:', userId);

                const params = buildQueryParams({ user_id: userId, limit_sessions: '3' });
                const response = await fetch(`${API_URL}/api/analytics/user-analytics/user-recent-sessions?${params.toString()}`);

                if (response.ok) {
                    const sessionsData = await response.json();

                    recentQueries = sessionsData.recent_sessions.map((q: any) => ({
                        query: q.query,
                        response: q.response,
                        timestamp: q.timestamp,
                        vote: q.vote || 0,
                        feedback: q.feedback || ''
                    }));

                    console.log('UserAnalytics - Recent sessions loaded:', recentQueries.length, 'queries from last 3 sessions');
                }
            } catch (queryError) {
                console.error('UserAnalytics - Error loading recent sessions:', queryError);
                recentQueries = [];
            }

            const detailData: UserDetailData = {
                user_id: userId,
                total_queries: userInfo.total_queries,
                total_sessions: userInfo.total_sessions,
                first_query: userInfo.first_query,
                last_active: userInfo.last_active,
                satisfaction_rate: userInfo.satisfaction_rate,
                thumbs_up_count: topUsers.find(u => u.user_id === userId)?.thumbs_up_count || 0,
                thumbs_down_count: topUsers.find(u => u.user_id === userId)?.thumbs_down_count || 0,
                most_active_hour: userInfo.most_active_hour,
                repeat_query_rate: userInfo.repeat_query_rate,
                recent_queries: recentQueries
            };

            setUserDetailData(detailData);
            console.log('UserAnalytics - User details loaded:', detailData);

        } catch (error) {
            console.error('UserAnalytics - Error loading user details:', error);
        } finally {
            setModalLoading(false);
        }
    };

    const handleExportUsers = async () => {
        try {
            setIsExporting(true);
            setExportMessage('');
            setExportType('');

            const params = buildQueryParams();
            const queryString = params.toString() ? `?${params.toString()}` : '';

            const response = await fetch(`${API_URL}/api/analytics/user-analytics/export/user-data${queryString}`, {
                method: 'HEAD'
            });

            if (!response.ok) {
                const errorData = await fetch(`${API_URL}/api/analytics/user-analytics/export/user-data${queryString}`)
                    .then(r => r.json())
                    .catch(() => ({ error: 'unknown' }));

                if (errorData.error === 'date_range_required') {
                    setExportType('error');
                    setExportMessage(errorData.message || 'Please select a date range to export user data.');
                    return;
                }
            }

            const url = `${API_URL}/api/analytics/user-analytics/export/user-data${queryString}`;
            window.open(url, '_blank');

            setExportType('success');
            setExportMessage('User data export started successfully! Your download should begin shortly.');
            console.log('UserAnalytics - User export initiated');

        } catch (error) {
            console.error('UserAnalytics - Export failed:', error);
            setExportType('error');
            setExportMessage('Export failed. Please try again or contact support.');
        } finally {
            setIsExporting(false);
        }
    };

    const dismissExportMessage = () => {
        setExportMessage('');
        setExportType('');
    };

    const handleSort = (field: keyof UserBreakdown) => {
        if (sortField === field) {
            setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
        } else {
            setSortField(field);
            setSortDirection('desc');
        }
    };

    const openUserModal = async (userId: string) => {
        setSelectedUser(userId);
        setShowUserModal(true);
        setUserDetailData(null);
        await loadUserDetails(userId);
    };

    const closeUserModal = () => {
        setSelectedUser(null);
        setShowUserModal(false);
        setUserDetailData(null);
    };

    const filteredUsers = userBreakdown
        .filter(user =>
            user.user_id.toLowerCase().includes(searchTerm.toLowerCase())
        )
        .sort((a, b) => {
            const aVal = a[sortField];
            const bVal = b[sortField];

            if (typeof aVal === 'number' && typeof bVal === 'number') {
                return sortDirection === 'asc' ? aVal - bVal : bVal - aVal;
            }

            const aStr = String(aVal).toLowerCase();
            const bStr = String(bVal).toLowerCase();

            if (sortDirection === 'asc') {
                return aStr.localeCompare(bStr);
            } else {
                return bStr.localeCompare(aStr);
            }
        });

    const totalPages = Math.ceil(filteredUsers.length / itemsPerPage);
    const startIndex = (currentPage - 1) * itemsPerPage;
    const endIndex = startIndex + itemsPerPage;
    const currentUsers = filteredUsers.slice(startIndex, endIndex);

    const engagementDistribution = [
        { name: 'High (20+ queries)', value: userBreakdown.filter(u => u.total_queries >= 20).length, color: '#FF6600' },
        { name: 'Medium (5-19 queries)', value: userBreakdown.filter(u => u.total_queries >= 5 && u.total_queries < 20).length, color: '#FFDBBB' },
        { name: 'Low (1-4 queries)', value: userBreakdown.filter(u => u.total_queries >= 1 && u.total_queries < 5).length, color: '#f2a24a' },
    ];

    if (loading) {
        return (
            <div className="user-analytics">
                <div className="loading-container">
                    <div className="loading-spinner"></div>
                    <h3>Loading User Analytics</h3>
                    <p>Loading user analytics data...</p>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="user-analytics">
                <div className="error-container">
                    <h3>Error Loading User Data</h3>
                    <p>{error}</p>
                    <button onClick={loadUserAnalyticsData} className="retry-btn">
                        <FiRefreshCw /> Try Again
                    </button>
                </div>
            </div>
        );
    }

    const overviewCards = [
        {
            title: "Total Users",
            value: userMetrics.total_unique_users.toLocaleString(),
            icon: <FiUsers />,
            desc: "Unique users served",
            trend: `${userMetrics.user_growth_rate.toFixed(1)}% growth`,
            color: "#FF6600"
        },
        {
            title: "Most Active User",
            value: userMetrics.most_active_user || "N/A",
            icon: <FiStar />,
            desc: "Highest query volume",
            trend: "Top performer",
            color: "#FF6600"
        },
        {
            title: "Avg Queries/User",
            value: userMetrics.avg_queries_per_user.toFixed(1),
            icon: <FiMessageSquare />,
            desc: "Questions per user",
            trend: `${userMetrics.avg_sessions_per_user.toFixed(1)} avg sessions`,
            color: "#FF6600"
        },
        {
            title: "Newest User",
            value: userMetrics.newest_user || "N/A",
            icon: <FiUserPlus />,
            desc: "Latest to join",
            trend: "Recent activity",
            color: "#FF6600"
        }
    ];

    return (
        <div className="user-analytics">
            {exportMessage && (
                <div className={`export-banner ${exportType}`}>
                    <div className="banner-content">
                        <div className="banner-message">
                            {exportType === 'success' ? (
                                <FiDownload className="banner-icon" />
                            ) : (
                                <FiX className="banner-icon" />
                            )}
                            <span>{exportMessage}</span>
                        </div>
                        <button className="banner-close" onClick={dismissExportMessage}>
                            <FiX />
                        </button>
                    </div>
                </div>
            )}

            {/* {(managerFilter || fstFilter) && (
                <div className="filter-status-bar">
                    <div className="filter-info">
                        <FiFilter className="filter-icon" />
                        <span>
                            {fstFilter
                                ? `Showing data for FST: ${fstFilter.full_name}`
                                : managerFilter
                                    ? `Showing data for Manager: ${managerFilter.name}'s team`
                                    : 'Filter applied'
                            }
                        </span>
                    </div>
                </div>
            )} */}

            <div className="dashboard-header">
                <div className="header-content">
                    <h1>User Analytics Summary</h1>
                    <p>Comprehensive insights into user behavior and engagement patterns</p>
                </div>
                <div className="header-actions">
                    <button
                        onClick={handleExportUsers}
                        className="export-button"
                        disabled={isExporting}
                    >
                        {isExporting ? <FiRefreshCw className="spinning" /> : <FiDownload />}
                        <span>{isExporting ? 'Exporting...' : 'Export Data'}</span>
                    </button>
                    <button onClick={loadUserAnalyticsData} className="refresh-button">
                        <FiRefreshCw />
                    </button>
                </div>
            </div>

            <div className="metrics-section">
                <div className="metrics-grid">
                    {overviewCards.map((card, index) => (
                        <div key={index} className="metric-card">
                            <div className="metric-header">
                                <div className="metric-icon" style={{ color: card.color }}>
                                    {card.icon}
                                </div>
                                <div className="metric-info">
                                    <h3>{card.title}</h3>
                                    <span className="metric-desc">{card.desc}</span>
                                </div>
                            </div>
                            <div className="metric-value">{card.value}</div>
                            <div className="metric-trend">{card.trend}</div>
                        </div>
                    ))}
                </div>
            </div>

            <div className="charts-section">
                <div className="section-title">
                    <h2>User Activity & Engagement Trends</h2>
                </div>

                <div className="charts-grid">
                    <div className="chart-card large-chart">
                        <div className="chart-header">
                            <h3>Daily Active Users</h3>
                            <div className="chart-info">
                                <span>{userActivityData.length} days</span>
                            </div>
                        </div>
                        <div className="chart-body">
                            <ResponsiveContainer width="100%" height="100%">
                                <LineChart data={userActivityData}>
                                    <XAxis
                                        dataKey="date"
                                        tick={{ fontSize: 12 }}
                                        stroke="#6c757d"
                                    />
                                    <YAxis
                                        tick={{ fontSize: 12 }}
                                        stroke="#6c757d"
                                    />
                                    <Tooltip
                                        contentStyle={{
                                            backgroundColor: 'white',
                                            border: '1px solid #dee2e6',
                                            borderRadius: '8px',
                                            boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)'
                                        }}
                                    />
                                    <Line
                                        type="monotone"
                                        dataKey="users"
                                        stroke="#FF6600"
                                        strokeWidth={3}
                                        dot={{ fill: '#FF6600', strokeWidth: 2, r: 4 }}
                                        activeDot={{ r: 6, stroke: '#007bff', strokeWidth: 2 }}
                                    />
                                </LineChart>
                            </ResponsiveContainer>
                        </div>
                    </div>

                    <div className="chart-card">
                        <div className="chart-header">
                            <h3>User Engagement Distribution</h3>
                        </div>
                        <div className="chart-body">
                            <ResponsiveContainer width="100%" height="100%">
                                <PieChart>
                                    <Pie
                                        data={engagementDistribution}
                                        cx="50%"
                                        cy="50%"
                                        innerRadius={60}
                                        outerRadius={100}
                                        dataKey="value"
                                    >
                                        {engagementDistribution.map((entry, index) => (
                                            <Cell key={`cell-${index}`} fill={entry.color} />
                                        ))}
                                    </Pie>
                                    <Tooltip />
                                </PieChart>
                            </ResponsiveContainer>
                        </div>
                        <div className="chart-legend">
                            {engagementDistribution.map((item, index) => (
                                <div key={index} className="legend-item">
                                    <div className="legend-dot" style={{ backgroundColor: item.color }}></div>
                                    <span>{item.name}</span>
                                    <strong>{item.value}</strong>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </div>

            {/* Top Users Section */}
            <div className="top-users-section">
                <div className="section-title">
                    <h2>Top 10 Most Active Users</h2>
                </div>
                <div className="users-grid">
                    {topUsers.map((user, index) => (
                        <div key={user.user_id} className="user-card">
                            <div className="user-rank">#{index + 1}</div>
                            <div className="user-details">
                                <div className="user-name">{user.user_id}</div>
                                <div className="user-stats">
                                    <span className="stat">
                                        <FiMessageSquare size={14} />
                                        {user.total_queries} queries
                                    </span>
                                    <span className="stat">
                                        <FiUsers size={14} />
                                        {user.total_sessions} sessions
                                    </span>
                                    <span className="stat">
                                        <FiThumbsUp size={14} />
                                        {user.satisfaction_rate.toFixed(1)}%
                                    </span>
                                </div>
                            </div>
                            <button
                                className="view-details-btn"
                                onClick={() => openUserModal(user.user_id)}
                            >
                                <FiEye />
                            </button>
                        </div>
                    ))}
                </div>
            </div>

            {/* Users Table */}
            <div className="table-section">
                <div className="table-header">
                    <div className="section-title">
                        <h2>All Users ({userBreakdown.length})</h2>
                    </div>
                    <div className="table-controls">
                        <div className="search-box">
                            <FiSearch />
                            <input
                                type="text"
                                placeholder="Search users..."
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                            />
                        </div>
                    </div>
                </div>

                <div className="table-container">
                    <table className="data-table">
                        <thead>
                            <tr>
                                <th onClick={() => handleSort('user_id')} className="sortable">
                                    User ID {sortField === 'user_id' && (sortDirection === 'asc' ? '↑' : '↓')}
                                </th>
                                <th onClick={() => handleSort('total_queries')} className="sortable">
                                    Queries {sortField === 'total_queries' && (sortDirection === 'asc' ? '↑' : '↓')}
                                </th>
                                <th onClick={() => handleSort('total_sessions')} className="sortable">
                                    Sessions {sortField === 'total_sessions' && (sortDirection === 'asc' ? '↑' : '↓')}
                                </th>
                                <th onClick={() => handleSort('avg_queries_per_day')} className="sortable">
                                    Avg/Day {sortField === 'avg_queries_per_day' && (sortDirection === 'asc' ? '↑' : '↓')}
                                </th>
                                <th onClick={() => handleSort('satisfaction_rate')} className="sortable">
                                    Satisfaction {sortField === 'satisfaction_rate' && (sortDirection === 'asc' ? '↑' : '↓')}
                                </th>
                                <th onClick={() => handleSort('last_active')} className="sortable">
                                    Last Active {sortField === 'last_active' && (sortDirection === 'asc' ? '↑' : '↓')}
                                </th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {currentUsers.map((user) => (
                                <tr key={user.user_id}>
                                    <td className="user-cell">{user.user_id}</td>
                                    <td><strong>{user.total_queries.toLocaleString()}</strong></td>
                                    <td>{user.total_sessions.toLocaleString()}</td>
                                    <td>{user.avg_queries_per_day.toFixed(1)}</td>
                                    <td>
                                        <span className={`badge ${user.satisfaction_rate >= 70 ? 'success' : user.satisfaction_rate >= 40 ? 'warning' : 'danger'}`}>
                                            {user.satisfaction_rate.toFixed(1)}%
                                        </span>
                                    </td>
                                    <td>{new Date(user.last_active).toLocaleDateString()}</td>
                                    <td>
                                        <button
                                            className="action-btn"
                                            onClick={() => openUserModal(user.user_id)}
                                            title="View user details"
                                        >
                                            <FiEye />
                                        </button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>

                {/* Pagination */}
                {totalPages > 1 && (
                    <div className="pagination">
                        <div className="pagination-info">
                            Showing {startIndex + 1}-{Math.min(endIndex, filteredUsers.length)} of {filteredUsers.length} users
                        </div>
                        <div className="pagination-controls">
                            <button
                                onClick={() => setCurrentPage(currentPage - 1)}
                                disabled={currentPage === 1}
                                className="pagination-btn"
                            >
                                <FiChevronLeft />
                            </button>
                            <span className="page-info">
                                Page {currentPage} of {totalPages}
                            </span>
                            <button
                                onClick={() => setCurrentPage(currentPage + 1)}
                                disabled={currentPage === totalPages}
                                className="pagination-btn"
                            >
                                <FiChevronRight />
                            </button>
                        </div>
                    </div>
                )}
            </div>

            {/* Enhanced User Details Modal */}
            {showUserModal && selectedUser && (
                <div className="modal-overlay" onClick={closeUserModal}>
                    <div className="modal-container" onClick={(e) => e.stopPropagation()}>
                        <div className="modal-header">
                            <h2>User Analytics: {selectedUser}</h2>
                            <button className="modal-close" onClick={closeUserModal}>
                                <FiX />
                            </button>
                        </div>

                        <div className="modal-content">
                            {modalLoading ? (
                                <div className="modal-loading">
                                    <div className="loading-spinner"></div>
                                    <p>Loading user details...</p>
                                </div>
                            ) : userDetailData ? (
                                <>
                                    {/* User Overview */}
                                    <div className="user-overview">
                                        <div className="overview-grid">
                                            <div className="overview-item">
                                                <FiMessageSquare className="overview-icon" />
                                                <div>
                                                    <div className="overview-value">{userDetailData.total_queries}</div>
                                                    <div className="overview-label">Total Queries</div>
                                                </div>
                                            </div>
                                            <div className="overview-item">
                                                <FiUsers className="overview-icon" />
                                                <div>
                                                    <div className="overview-value">{userDetailData.total_sessions}</div>
                                                    <div className="overview-label">Total Sessions</div>
                                                </div>
                                            </div>
                                            <div className="overview-item">
                                                <FiThumbsUp className="overview-icon" />
                                                <div>
                                                    <div className="overview-value">{userDetailData.satisfaction_rate.toFixed(1)}%</div>
                                                    <div className="overview-label">Satisfaction Rate</div>
                                                </div>
                                            </div>
                                            <div className="overview-item">
                                                <FiClock className="overview-icon" />
                                                <div>
                                                    <div className="overview-value">{userDetailData.most_active_hour}:00</div>
                                                    <div className="overview-label">Most Active Hour</div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>

                                    {/* User Details */}
                                    <div className="user-details-grid">
                                        <div className="detail-section">
                                            <h3>Activity Timeline</h3>
                                            <div className="timeline-info">
                                                <div className="timeline-item">
                                                    <strong>First Query:</strong> {new Date(userDetailData.first_query).toLocaleString()}
                                                </div>
                                                <div className="timeline-item">
                                                    <strong>Last Active:</strong> {new Date(userDetailData.last_active).toLocaleString()}
                                                </div>
                                                <div className="timeline-item">
                                                    <strong>Repeat Query Rate:</strong> {userDetailData.repeat_query_rate.toFixed(1)}%
                                                </div>
                                            </div>
                                        </div>

                                        <div className="detail-section">
                                            <h3>Feedback Summary</h3>
                                            <div className="feedback-stats">
                                                <div className="feedback-item positive">
                                                    <FiThumbsUp />
                                                    <span>{userDetailData.thumbs_up_count} Positive</span>
                                                </div>
                                                <div className="feedback-item negative">
                                                    <FiThumbsUp style={{ transform: 'rotate(180deg)' }} />
                                                    <span>{userDetailData.thumbs_down_count} Negative</span>
                                                </div>
                                            </div>
                                        </div>
                                    </div>

                                    {/* Recent Queries */}
                                    <div className="recent-queries">
                                        <h3>Recent Query History</h3>
                                        {userDetailData.recent_queries.length > 0 ? (
                                            <div className="queries-list">
                                                {userDetailData.recent_queries.map((query, index) => (
                                                    <div key={index} className="query-item">
                                                        <div className="query-header">
                                                            <span className="query-time">
                                                                {new Date(query.timestamp).toLocaleString()}
                                                            </span>
                                                            {query.vote === 1 && (
                                                                <span className="vote-badge positive">
                                                                    <FiThumbsUp size={12} /> Positive
                                                                </span>
                                                            )}
                                                            {query.vote === -1 && (
                                                                <span className="vote-badge negative">
                                                                    <FiThumbsUp size={12} style={{ transform: 'rotate(180deg)' }} /> Negative
                                                                </span>
                                                            )}
                                                        </div>
                                                        <div className="query-content">
                                                            <div className="query-text">
                                                                <strong>Q:</strong> {query.query}
                                                            </div>
                                                            <div className="response-text">
                                                                <strong>A:</strong> {query.response.slice(0, 200)}
                                                                {query.response.length > 200 && '...'}
                                                            </div>
                                                            {query.feedback && (
                                                                <div className="query-feedback">
                                                                    <strong>Feedback:</strong> {query.feedback}
                                                                </div>
                                                            )}
                                                        </div>
                                                    </div>
                                                ))}
                                            </div>
                                        ) : (
                                            <div className="no-queries">
                                                <FiMessageSquare size={24} />
                                                <p>No recent queries found for this user</p>
                                            </div>
                                        )}
                                    </div>
                                </>
                            ) : (
                                <div className="modal-error">
                                    <p>Unable to load user details. Please try again.</p>
                                </div>
                            )}
                        </div>

                        <div className="modal-footer">
                            <button className="btn btn-secondary" onClick={closeUserModal}>
                                Close
                            </button>
                            <button
                                className="btn btn-primary"
                                onClick={() => {
                                    const params = buildQueryParams({ user_id: selectedUser });
                                    const url = `${API_URL}/api/analytics/user-analytics/export/user-data?${params.toString()}`;
                                    window.open(url, '_blank');
                                }}
                            >
                                <FiDownload size={16} />
                                Export User Data
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default UserAnalyticsDashboard;