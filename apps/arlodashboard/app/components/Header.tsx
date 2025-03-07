import React, { useState, useEffect } from 'react';
import dayjs from 'dayjs';

import './Header.css';

interface HeaderProps {
    onDateChange: (fromDate: string, toDate: string) => void;
}

const Header: React.FC<HeaderProps> = ({ onDateChange }) => {
    const [selectedOption, setSelectedOption] = useState<string>('today');
    const [showCalendar, setShowCalendar] = useState<boolean>(false);
    const [fromDate, setFromDate] = useState<string>('');
    const [toDate, setToDate] = useState<string>('');
    const [isDisabled, setIsDisabled] = useState<boolean>(true);

    const updateDateRange = (option: string): void => {
        const today = dayjs();

        switch (option) {
            case 'today':
                const todayDate = today.format('YYYY-MM-DD');
                setFromDate(todayDate);
                setToDate(todayDate);
                setIsDisabled(true);
                onDateChange(todayDate, todayDate); // Pass the selected range
                break;
            case 'this_week':
                const startOfWeek = today.startOf('week').format('YYYY-MM-DD');
                const endOfWeek = today.endOf('week').format('YYYY-MM-DD');
                setFromDate(startOfWeek);
                setToDate(endOfWeek);
                setIsDisabled(true);
                onDateChange(startOfWeek, endOfWeek);
                break;
            case 'this_month':
                const startOfMonth = today.startOf('month').format('YYYY-MM-DD');
                const endOfMonth = today.endOf('month').format('YYYY-MM-DD');
                setFromDate(startOfMonth);
                setToDate(endOfMonth);
                setIsDisabled(true);
                onDateChange(startOfMonth, endOfMonth);
                break;
            case 'custom':
                setShowCalendar(true);
                setIsDisabled(false);
                break;
            default:
                setFromDate('');
                setToDate('');
        }
    };

    const handleDropdownChange = (e: React.ChangeEvent<HTMLSelectElement>): void => {
        const value = e.target.value;
        setSelectedOption(value);

        if (value !== 'custom') {
            setShowCalendar(false);
            updateDateRange(value);
        } else {
            setShowCalendar(true);
            setIsDisabled(false);
        }
    };

    useEffect(() => {
        updateDateRange(selectedOption);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    const handleCustomDateChange = (type: 'from' | 'to', value: string): void => {
        if (type === 'from') setFromDate(value);
        if (type === 'to') setToDate(value);

        if (type === 'to' && fromDate) {
            onDateChange(fromDate, value);
        }
    };

    return (
        <div className="header">
            <h1 className="title">Arlo Dashboard</h1>
            <div className="rightContainer">
                <select value={selectedOption} onChange={handleDropdownChange} className="dropdown">
                    <option value="today">Today</option>
                    <option value="this_week">This Week</option>
                    <option value="this_month">This Month</option>
                    <option value="custom">Custom</option>
                </select>

                <div className="dateContainer">
                    <input
                        type="date"
                        disabled={isDisabled}
                        className="dateInput"
                        value={fromDate}
                        onChange={(e) => handleCustomDateChange('from', e.target.value)}
                    />
                    <span className="toText">to</span>
                    <input
                        type="date"
                        disabled={isDisabled}
                        className="dateInput"
                        value={toDate}
                        onChange={(e) => handleCustomDateChange('to', e.target.value)}
                    />
                </div>
            </div>
        </div>
    );
};

export default Header;