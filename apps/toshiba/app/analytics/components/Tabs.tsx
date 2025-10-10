"use client";

import React, { useState, useEffect } from 'react';
import './Tabs.scss';
import Summary from './TabComponents/Summary';
import QueryAnalytics from './TabComponents/QueryAnalytics';
import ProductAnalysis from './TabComponents/ProductAnalysis';
import CustomerAnalytics from './TabComponents/CustomerAnalytics';
import UserAnalytics from './TabComponents/UserAnalytics';

const tabOptions = [
    'Summary',
    'Product Analysis',
    'Customer Analytics',
    'Query Analytics',
    'User Analytics'
];

export interface DateFilters {
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

interface UserAnalyticsManagerFilter {
    id: number;
    name: string;
}

interface UserAnalyticsFSTFilter {
    id: number;
    full_name: string;
    fst_email: string;
}

const getJuly28DefaultDates = (): DateFilters => {
    return {
        startDate: '2025-07-28',
        endDate: ''
    };
};

const Tabs = () => {
    const [activeTab, setActiveTab] = useState('Summary');

    const [serviceRequestFilters, setServiceRequestFilters] = useState<DateFilters>({
        startDate: '',
        endDate: ''
    });
    const [queryAnalyticsFilters, setQueryAnalyticsFilters] = useState<DateFilters>(
        getJuly28DefaultDates()
    );
    const [userAnalyticsFilters, setUserAnalyticsFilters] = useState<DateFilters>(
        getJuly28DefaultDates()
    );

    const [managerFilter, setManagerFilter] = useState<ManagerFilter>({
        managerId: null,
        managerName: "All Managers"
    });

    const [fstFilter, setFSTFilter] = useState<FSTFilter>({
        fstId: null,
        fstName: "All FSTs"
    });

    const [managers, setManagers] = useState<any[]>([]);
    const [fsts, setFSTs] = useState<any[]>([]);
    const [loadingFSTs, setLoadingFSTs] = useState(false);

    const [serviceRequestQuickFilter, setServiceRequestQuickFilter] = useState('All Time');
    const [queryAnalyticsQuickFilter, setQueryAnalyticsQuickFilter] = useState('Custom');
    const [userAnalyticsQuickFilter, setUserAnalyticsQuickFilter] = useState('Custom');

    useEffect(() => {
        loadManagerGroups();
    }, []);

    useEffect(() => {
        if (managerFilter.managerId) {
            loadFSTsForManager(managerFilter.managerId);
        } else {
            setFSTs([]);
            setFSTFilter({ fstId: null, fstName: "All FSTs" });
        }
    }, [managerFilter.managerId]);

    const loadManagerGroups = async () => {
        try {
            const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
            const response = await fetch(`${API_URL}/api/analytics/technicians/manager-groups`);
            if (response.ok) {
                const managerData = await response.json();
                setManagers(managerData);
                console.log('Manager groups loaded:', managerData);
            }
        } catch (error) {
            console.error('Error loading manager groups:', error);
            setManagers([
                { id: 1, manager_name: "Anthony Setaro", region: "East", fst_count: 26 },
                { id: 2, manager_name: "Howard Goldenberg", region: "East", fst_count: 22 },
                { id: 3, manager_name: "Ian Sauter", region: "Unknown", fst_count: 21 }
            ]);
        }
    };

    const loadFSTsForManager = async (managerId: number) => {
        try {
            setLoadingFSTs(true);
            const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
            const response = await fetch(`${API_URL}/api/analytics/technicians/fsts-by-manager/${managerId}`);

            if (response.ok) {
                const fstData = await response.json();
                console.log(`FSTs loaded for manager ${managerId}:`, fstData.length, 'FSTs');
                setFSTs(fstData);
            } else {
                console.error('Failed to load FSTs:', response.status);
                setFSTs([]);
            }
        } catch (error) {
            console.error('Error loading FSTs:', error);
            setFSTs([]);
        } finally {
            setLoadingFSTs(false);
        }
    };

    const isQueryAnalyticsTab = activeTab === 'Query Analytics';
    const isUserAnalyticsTab = activeTab === 'User Analytics';

    let currentFilters;
    let currentQuickFilter;

    if (isQueryAnalyticsTab) {
        currentFilters = queryAnalyticsFilters;
        currentQuickFilter = queryAnalyticsQuickFilter;
    } else if (isUserAnalyticsTab) {
        currentFilters = userAnalyticsFilters;
        currentQuickFilter = userAnalyticsQuickFilter;
    } else {
        currentFilters = serviceRequestFilters;
        currentQuickFilter = serviceRequestQuickFilter;
    }

    const handleQuickFilterChange = (value: string) => {
        const today = new Date();
        let startDate = '';
        let endDate = today.toISOString().split('T')[0];

        switch (value) {
            case 'Last 7 Days':
                const weekAgo = new Date(today);
                weekAgo.setDate(today.getDate() - 7);
                startDate = weekAgo.toISOString().split('T')[0];
                break;
            case 'Last 30 Days':
                const monthAgo = new Date(today);
                monthAgo.setDate(today.getDate() - 30);
                startDate = monthAgo.toISOString().split('T')[0];
                break;
            case 'July 28th Default':
                const defaultDates = getJuly28DefaultDates();
                startDate = defaultDates.startDate;
                endDate = defaultDates.endDate;
                break;
            case 'All Time':
            default:
                startDate = '';
                endDate = '';
                break;
        }

        const newFilters = { startDate, endDate };

        if (isQueryAnalyticsTab) {
            setQueryAnalyticsFilters(newFilters);
            setQueryAnalyticsQuickFilter(value);
        } else if (isUserAnalyticsTab) {
            setUserAnalyticsFilters(newFilters);
            setUserAnalyticsQuickFilter(value);
        } else {
            setServiceRequestFilters(newFilters);
            setServiceRequestQuickFilter(value);
        }
    };

    const handleStartDateChange = (date: string) => {
        const newFilters = { ...currentFilters, startDate: date };

        if (isQueryAnalyticsTab) {
            setQueryAnalyticsFilters(newFilters);
            setQueryAnalyticsQuickFilter('Custom');
        } else if (isUserAnalyticsTab) {
            setUserAnalyticsFilters(newFilters);
            setUserAnalyticsQuickFilter('Custom');
        } else {
            setServiceRequestFilters(newFilters);
            setServiceRequestQuickFilter('Custom');
        }
    };

    const handleEndDateChange = (date: string) => {
        const newFilters = { ...currentFilters, endDate: date };

        if (isQueryAnalyticsTab) {
            setQueryAnalyticsFilters(newFilters);
            setQueryAnalyticsQuickFilter('Custom');
        } else if (isUserAnalyticsTab) {
            setUserAnalyticsFilters(newFilters);
            setUserAnalyticsQuickFilter('Custom');
        } else {
            setServiceRequestFilters(newFilters);
            setServiceRequestQuickFilter('Custom');
        }
    };

    const handleManagerSelect = (event: React.ChangeEvent<HTMLSelectElement>) => {
        const managerId = event.target.value ? parseInt(event.target.value) : null;
        const manager = managers.find(m => m.id === managerId);
        setManagerFilter({
            managerId,
            managerName: manager?.manager_name || "All Managers"
        });

        setFSTFilter({ fstId: null, fstName: "All FSTs" });
        console.log('Manager filter changed:', manager ? manager.manager_name : "All Managers");
    };

    const handleFSTSelect = (event: React.ChangeEvent<HTMLSelectElement>) => {
        const fstId = event.target.value ? parseInt(event.target.value) : null;
        const fst = fsts.find(f => f.id === fstId);
        setFSTFilter({
            fstId,
            fstName: fst?.full_name || "All FSTs"
        });
        console.log('FST filter changed:', fst ? fst.full_name : "All FSTs");
    };

    const clearFilters = () => {
        if (isQueryAnalyticsTab) {
            setQueryAnalyticsFilters(getJuly28DefaultDates());
            setQueryAnalyticsQuickFilter('July 28th Default');
        } else if (isUserAnalyticsTab) {
            setUserAnalyticsFilters(getJuly28DefaultDates());
            setUserAnalyticsQuickFilter('July 28th Default');
        } else {
            setServiceRequestFilters({ startDate: '', endDate: '' });
            setServiceRequestQuickFilter('All Time');
        }

        setManagerFilter({
            managerId: null,
            managerName: "All Managers"
        });
        setFSTFilter({
            fstId: null,
            fstName: "All FSTs"
        });
    };

    const getUserAnalyticsManagerFilter = (): UserAnalyticsManagerFilter | null => {
        if (!managerFilter.managerId) return null;
        const manager = managers.find(m => m.id === managerFilter.managerId);
        return manager ? {
            id: manager.id,
            name: manager.manager_name
        } : null;
    };

    const getUserAnalyticsFSTFilter = (): UserAnalyticsFSTFilter | null => {
        if (!fstFilter.fstId) return null;
        const fst = fsts.find(f => f.id === fstFilter.fstId);
        return fst ? {
            id: fst.id,
            full_name: fst.full_name,
            fst_email: fst.fst_email
        } : null;
    };

    const renderTabContent = () => {
        switch (activeTab) {
            case 'Summary':
                return (
                    <Summary
                        dateFilters={serviceRequestFilters}
                        managerFilter={managerFilter}
                        fstFilter={fstFilter}
                    />
                );
            case 'Product Analysis':
                return (
                    <ProductAnalysis
                        dateFilters={serviceRequestFilters}
                        managerFilter={managerFilter}
                        fstFilter={fstFilter}
                    />
                );
            case 'Customer Analytics':
                return (
                    <CustomerAnalytics
                        dateFilters={serviceRequestFilters}
                        managerFilter={managerFilter}
                        fstFilter={fstFilter}
                    />
                );
            case 'Query Analytics':
                return (
                    <QueryAnalytics
                        dateFilters={queryAnalyticsFilters}
                        managerFilter={managerFilter}
                        fstFilter={fstFilter}
                    />
                );
            case 'User Analytics':
                return (
                    <UserAnalytics
                        dateFilters={userAnalyticsFilters}
                        managerFilter={getUserAnalyticsManagerFilter()}
                        fstFilter={getUserAnalyticsFSTFilter()}
                    />
                );
            default:
                return <div>No content available</div>;
        }
    };

    const getFilterLabel = () => {
        if (isQueryAnalyticsTab) return 'Query Data Filter:';
        if (isUserAnalyticsTab) return 'User Data Filter:';
        return 'Service Request Filter:';
    };

    const getDropdownOptions = () => {
        const baseOptions = ['All Time', 'Last 30 Days', 'Last 7 Days', 'Custom'];

        if (isQueryAnalyticsTab || isUserAnalyticsTab) {
            return ['July 28th Default', ...baseOptions];
        }

        return baseOptions;
    };

    const shouldShowManagerFilter = () => {
        return ['Summary', 'Product Analysis', 'Customer Analytics', 'Query Analytics', 'User Analytics'].includes(activeTab);
    };

    const hasActiveFilters = () => {
        const hasDateFilters = currentFilters.startDate || currentFilters.endDate;
        const hasManagerFilter = managerFilter.managerId !== null;
        const hasFSTFilter = fstFilter.fstId !== null;
        return hasDateFilters || hasManagerFilter || hasFSTFilter;
    };

    return (
        <div className="tabs-container">
            <div className="tabs-header">
                <div className="tabs-left">
                    {tabOptions.map((tab) => (
                        <button
                            key={tab}
                            className={`tab-button ${activeTab === tab ? 'active' : ''}`}
                            onClick={() => setActiveTab(tab)}
                        >
                            {tab}
                        </button>
                    ))}
                </div>

                <div className="tabs-right">
                    <div className="filter-label">
                        {getFilterLabel()}
                    </div>

                    <select
                        className="time-dropdown"
                        value={currentQuickFilter}
                        onChange={(e) => handleQuickFilterChange(e.target.value)}
                    >
                        {getDropdownOptions().map(option => (
                            <option key={option} value={option}>{option}</option>
                        ))}
                    </select>

                    <input
                        type="date"
                        className="date-picker"
                        value={currentFilters.startDate}
                        onChange={(e) => handleStartDateChange(e.target.value)}
                    />
                    <span>to</span>
                    <input
                        type="date"
                        className="date-picker"
                        value={currentFilters.endDate}
                        onChange={(e) => handleEndDateChange(e.target.value)}
                    />

                    {shouldShowManagerFilter() && (
                        <select
                            className="time-dropdown"
                            value={managerFilter.managerId || ""}
                            onChange={handleManagerSelect}
                        >
                            <option value="">All Managers</option>
                            {managers.map(manager => (
                                <option key={manager.id} value={manager.id}>
                                    {manager.manager_name} ({manager.fst_count} FSTs)
                                </option>
                            ))}
                        </select>
                    )}

                    {shouldShowManagerFilter() && managerFilter.managerId && (
                        <select
                            className="time-dropdown"
                            value={fstFilter.fstId || ""}
                            onChange={handleFSTSelect}
                            disabled={loadingFSTs}
                        >
                            <option value="">
                                {loadingFSTs ? 'Loading FSTs...' : `All FSTs (${fsts.length})`}
                            </option>
                            {fsts.map(fst => (
                                <option key={fst.id} value={fst.id}>
                                    {fst.full_name}
                                </option>
                            ))}
                        </select>
                    )}

                    {/* <button
                        className="clear-button"
                        onClick={clearFilters}
                    >
                        {(isQueryAnalyticsTab || isUserAnalyticsTab) ? 'Reset to Default' : 'Clear'}
                    </button> */}
                </div>
            </div>

            {/* {hasActiveFilters() && (
                <div className="active-filter-banner">
                    Active Filters:
                    {currentFilters.startDate && ` From: ${currentFilters.startDate}`}
                    {currentFilters.endDate && ` To: ${currentFilters.endDate}`}
                    {managerFilter.managerId && ` | Manager: ${managerFilter.managerName}`}
                    {fstFilter.fstId && ` | FST: ${fstFilter.fstName}`}
                </div>
            )} */}

            <div>
                {renderTabContent()}
            </div>

            <style jsx>{`
                .active-filter-banner {
                    background-color: #e3f2fd;
                    color: #1976d2;
                    padding: 8px 16px;
                    margin-bottom: 20px;
                    border-left: 4px solid #1976d2;
                    font-size: 14px;
                    font-weight: 500;
                }
                
                .time-dropdown {
                    min-width: 140px;
                }
                
                .time-dropdown:disabled {
                    opacity: 0.6;
                    cursor: not-allowed;
                }
            `}</style>
        </div>
    );
};

export default Tabs;