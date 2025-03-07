import React, { useState } from 'react';
import Agents from "./Agents";
import Problems from "./Problems";
import Products from "./Products";
import RootCause from "./RootCause";
import { Summary } from "./Summary/Summary";
import { DateRange } from "./Summary/types";

interface TabComponentProps {
    dateRange: DateRange;
}

interface TabPanelProps {
    children: React.ReactNode;
    value: number;
    index: number;
}

interface TabDetail {
    label: string;
    component: React.ReactNode;
}

function TabPanel({ children, value, index, ...other }: TabPanelProps) {
    return (
        <div
            role="tabpanel"
            hidden={value !== index}
            id={`simple-tabpanel-${index}`}
            aria-labelledby={`simple-tab-${index}`}
            className="h-full"
            {...other}
        >
            {value === index && (
                <div className="bg-white h-full border-t-0 border border-gray-300">
                    {children}
                </div>
            )}
        </div>
    );
}

const TabComponent: React.FC<TabComponentProps> = ({ dateRange }) => {
    const [value, setValue] = useState<number>(0);

    const handleChange = (index: number) => {
        setValue(index);
    };

    const tabDetails: TabDetail[] = [
        { label: 'SUMMARY', component: <Summary dateRange={dateRange} /> },
        { label: 'PROBLEMS', component: <Problems dateRange={dateRange} /> },
        { label: 'ROOT CAUSE', component: <RootCause dateRange={dateRange} /> },
        { label: 'PRODUCTS', component: <Products dateRange={dateRange} /> },
        { label: 'AGENTS', component: <Agents dateRange={dateRange} /> },
    ];

    return (
        <div className="bg-gray-300 w-full">
            <div className="w-full h-full">
                <div className="flex">
                    {tabDetails.map((tab, index) => (
                        <button
                            key={tab.label}
                            onClick={() => handleChange(index)}
                            className={`
                            px-8 py-3 text-sm font-medium border-t border-r border-l border-gray-400
                            min-w-[120px] transition-colors duration-200 ease-in-out
                            ${value === index
                                    ? 'bg-white text-blue-700 border-b-0 border-t-2 border-t-blue-700'
                                    : 'bg-gray-500 text-white border-b border-gray-400 hover:bg-gray-600'}
                            `}
                        >
                            {tab.label}
                        </button>
                    ))}
                    <div className="flex-grow border-b border-gray-400"></div>
                </div>
                {tabDetails.map((tab, index) => (
                    <TabPanel key={tab.label} value={value} index={index}>
                        {tab.component}
                    </TabPanel>
                ))}
            </div>
        </div>
    );
};

export default TabComponent;