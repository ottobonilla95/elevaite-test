import React, { useState, useEffect } from 'react';
import dayjs from 'dayjs';

import './Header.css';

const Header = ({ onDateChange }) => {
    const [selectedOption, setSelectedOption] = useState('today');
    const [showCalendar, setShowCalendar] = useState(false);
    const [fromDate, setFromDate] = useState('');
    const [toDate, setToDate] = useState('');
    const [isDisabled, setIsDisabled] = useState(true);

    const updateDateRange = (option) => {
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

    const handleDropdownChange = (e) => {
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

    const handleCustomDateChange = (type, value) => {
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
                    <input type="date" disabled={isDisabled} className="dateInput"
                        value={fromDate}
                        onChange={(e) => handleCustomDateChange('from', e.target.value)}
                    />
                    <span className="toText">to</span>
                    <input type="date" disabled={isDisabled} className="dateInput"
                        value={toDate}
                        onChange={(e) => handleCustomDateChange('to', e.target.value)}
                    />
                </div>
            </div>
        </div>
    );
};

export default Header;