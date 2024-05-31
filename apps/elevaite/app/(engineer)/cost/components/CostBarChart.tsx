"use client";
import { useThemes } from '@repo/ui/contexts';
import { BarElement, CategoryScale, Chart as ChartJS, Legend, LinearScale, Title, Tooltip, type TooltipItem, } from 'chart.js';
import { useEffect, useState } from 'react';
import { Bar } from "react-chartjs-2";
import { useCost } from "../../../lib/contexts/CostContext";
import "./CostBarChart.scss";

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);





export function CostBarChart(): JSX.Element {
    const costContext = useCost();
    const themeContext = useThemes();
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
                callbacks: {
                    beforeBody: () => "\n",
                    afterBody: () => "\n",
                    footer: getFooter,
                    label: formatLabelNumber,
                },
                filter: filterTooltip,
            }
        }
    };

    useEffect(() => {
        setBarLabels(costContext.costDetails.uniqueProjects ?? []);
    }, [costContext.costDetails.uniqueProjects]);


    // FILTER FUNCTIONS

    function getFooter(tooltipItems: TooltipItem<"bar">[]): string {
        let totalCost = 0;      
        tooltipItems.forEach((tooltipItem: TooltipItem<"bar">) => {
            totalCost += tooltipItem.parsed.y;
        });
        return `Total Cost:    $ ${totalCost.toLocaleString(undefined, {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        })}`;
    };

    function formatLabelNumber(tooltipItem: TooltipItem<"bar">): string {
        return `${tooltipItem.dataset.label ?? ""}:    $ ${parseFloat(tooltipItem.formattedValue).toLocaleString(undefined, {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        })}`;
    }

    function formatChartYAxis(value: string): string {
        return `$ ${parseFloat(value).toLocaleString(undefined, {
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
        })}`;
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
                            data: costContext.getCostsOfModelPerProject(model),
                            backgroundColor: costContext.getBarColor(model),
                        }; })                        
                    }}
                    options={options}
                />
            </div>

        </div>
    );
}