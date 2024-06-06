"use client";
import { useThemes } from '@repo/ui/contexts';
import { BarElement, CategoryScale, Chart as ChartJS, Legend, LinearScale, Title, Tooltip, type TooltipItem, } from 'chart.js';
import { useEffect, useState } from 'react';
import { Bar } from "react-chartjs-2";
import { costBarChartAxisValues, useCost } from "../../../lib/contexts/CostContext";
import "./CostBarChart.scss";

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);





export function CostBarChart(): JSX.Element {
    const costContext = useCost();
    const themeContext = useThemes();
    // const barChartRef = useRef<ChartJS<"bar", number[], string> | undefined | null>(null);
    const [barLabels, setBarLabels] = useState<string[]>([]);


    const options = {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
            x: {
                stacked: true,
                ticks: {
                    color: themeContext.text,
                },
                grid: {
                    color: themeContext.borderColor,
                },
            },
            y: {
                stacked: true,
                ticks: {
                    color: themeContext.secondaryText,
                    callback: formatChartYAxis
                },
                grid: {
                    color: themeContext.borderColor,
                }
            },
        },
        interaction: {
            intersect: false,
            mode: "index" as const,
        },
        plugins: {
            tooltip: {
                 // The default "average" for position is better, but it has a critical bug:
                 // When you scroll over it before the chart has loaded, it throws a .reduce without first value error.
                position: "nearest" as const,
                titleMarginBottom: 20,
                footerMarginTop: 20,
                callbacks: {
                    footer: getFooter,
                    label: formatLabelNumber,
                },
                filter: filterTooltip,
            }
        }
    };

    useEffect(() => {
        if (costContext.costBarChartAxis === costBarChartAxisValues.TOKENS) {
            setBarLabels(costContext.costDetails.uniqueProjects ? costContext.costDetails.uniqueProjects.map(item => [`${item} In`, `${item} Out`]).flat() : []);
        } else {
            setBarLabels(costContext.costDetails.uniqueProjects ?? []);
        }
    }, [costContext.costDetails.uniqueProjects, costContext.costBarChartAxis]);




    // FILTER FUNCTIONS

    function getFooter(tooltipItems: TooltipItem<"bar">[]): string {
        let totalAmount = 0;      
        tooltipItems.forEach((tooltipItem: TooltipItem<"bar">) => {
            totalAmount += tooltipItem.parsed.y;
        });
        switch (costContext.costBarChartAxis) {
            case costBarChartAxisValues.TOKENS: return `Total Tokens:    ${totalAmount.toLocaleString(undefined, {
                minimumFractionDigits: 0,
                maximumFractionDigits: 0
            })}`;
            case costBarChartAxisValues.GPU: return `Total GPU Usage:    ${totalAmount.toLocaleString(undefined, {
                minimumFractionDigits: 0,
                maximumFractionDigits: 2
            })} mins`;
            case costBarChartAxisValues.COST: return `Total Cost:    $ ${totalAmount.toLocaleString(undefined, {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2
            })}`;
        }
    };

    function formatLabelNumber(tooltipItem: TooltipItem<"bar">): string {
        const value = tooltipItem.raw as number;
        if (!value || isNaN(value)) return "";
        switch (costContext.costBarChartAxis) {
            case costBarChartAxisValues.TOKENS: return `${tooltipItem.dataset.label ?? ""}:    ${value.toLocaleString(undefined, {
                minimumFractionDigits: 0,
                maximumFractionDigits: 0
            })}`;
            case costBarChartAxisValues.GPU: return `${tooltipItem.dataset.label ?? ""}:    ${value.toLocaleString(undefined, {
                minimumFractionDigits: 0,
                maximumFractionDigits: 2
            })} mins`;
            case costBarChartAxisValues.COST: return `${tooltipItem.dataset.label ?? ""}:    $ ${value.toLocaleString(undefined, {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2
            })}`;
        }
    }

    function formatChartYAxis(value: string): string {
        const formattedValue = parseFloat(value).toLocaleString(undefined, {
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
        });

        switch (costContext.costBarChartAxis) {
            case costBarChartAxisValues.TOKENS: return `${formattedValue} tkn`;
            case costBarChartAxisValues.GPU: return `${formattedValue} mins`;
            case costBarChartAxisValues.COST: return `$ ${formattedValue}`;
        }
    }

    function filterTooltip(tooltipItem: TooltipItem<"bar">): boolean {
        return tooltipItem.raw !== 0;
    }    

    //////////////



    return (
        <div className="cost-bar-chart-container">

            <div className="cost-bar-wrapper">
                <Bar
                    data={{
                        labels: barLabels,
                        datasets: !costContext.costDetails.uniqueModels ? [] : 
                        costContext.costDetails.uniqueModels.map(model => { return {
                            label: model,
                            data: costContext.getValueOfModelPerProject(model, costContext.costBarChartAxis),
                            backgroundColor: costContext.getBarColor(model),
                        }; })                        
                    }}
                    options={options}
                />
            </div>

        </div>
    );
}