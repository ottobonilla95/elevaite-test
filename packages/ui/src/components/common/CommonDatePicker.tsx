"use client";
import type { JSX } from "react";
import { useEffect, useState } from "react";
import DatePicker from "react-datepicker";
import "react-datepicker/dist/react-datepicker.css";
import "./CommonDatePicker.scss";


interface CommonDatePickerProps {
    selectedDate?: string;
    onDateChange: (IsoDate: string) => void;
    monthOnly?: boolean;
    customInput?: JSX.Element;
}

export function CommonDatePicker(props: CommonDatePickerProps): JSX.Element {
    const [selectedDate, setSelectedDate] = useState<Date>(new Date());


    useEffect(() => {
        setSelectedDate(props.selectedDate ? new Date(props.selectedDate) : new Date());
    }, [props.selectedDate]);


    function handleDateChange(date: Date): void {
        props.onDateChange(date.toISOString());
    }



    return (
        <div className="common-date-picker-container">
            <DatePicker
                selected={selectedDate}
                onChange={handleDateChange}
                showMonthYearPicker={props.monthOnly}
                showFullMonthYearPicker={props.monthOnly}
                dateFormat="MMMM yyyy"
                customInput={props.customInput}
            />
        </div>
    );
}