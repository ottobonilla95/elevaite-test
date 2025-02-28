"use client";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../components/ui/table";
import { CampaignPerformance } from "../types";
import { useState } from "react";

const CampaignTable = ({ performanceData }: { performanceData: CampaignPerformance[] }) => {
  console.log("The data is received:", performanceData);
  if (!performanceData?.length) return <div className="text-muted-foreground">No performance data available</div>;

  const [expandedRow, setExpandedRow] = useState<string | null>(null);

  const metrics = [
    { label: "Campaign Name", key: "Campaign_Name", format: "text" },
    { label: "Duration (days)", key: "Duration", format: "number" },
    { label: "Budget", key: "Budget", format: "number" },
    { label: "Clickable Impressions", key: "Booked_Impressions", format: "number" },
    { label: "Delivered Trips", key: "Clickable_Impressions", format: "number" },
    { label: "Clicks", key: "Clicks", format: "number" },
    { label: "CTR", key: "Conversion", format: "percentage" },
    { label: "eCPM", key: "ECPM", format: "number" },
    { label: "Creative Insights", key: "Insights", format: "text" },
  ];

  const handleRowClick = (campaignName: string) => {
    setExpandedRow(expandedRow === campaignName ? null : campaignName);
  };

  return (
      <div className="rounded-md border flex h-full shadow-[inset_-10px_0_12px_-8px_rgba(0,0,0,0.1)]">
        <Table className="min-w-[800px]">
          <TableHeader className="sticky top-0 bg-background z-20">
            <TableRow>
              {metrics.map((metric) => (
                <TableHead
                  key={metric.key}
                  className={`min-w-[150px] max-w-[200px] p-4 whitespace-nowrap border-l `}
                  title={metric.label} 
                >
                  {metric.label}
                </TableHead>
              ))}
            </TableRow>
          </TableHeader>

          <TableBody>
            {performanceData.map((campaign) => (
              <TableRow
                key={campaign.Campaign_Name}
                onClick={() => handleRowClick(campaign.Campaign_Name)}
                className="cursor-pointer"
              >
                {metrics.map((metric) => {
                  const value = campaign[metric.key as keyof CampaignPerformance];

                  // Check if value is defined and handle accordingly
                  let displayValue = "-"; // Default value if data is missing
                  if (value !== undefined && value !== null) {
                    if (metric.format === "percentage") {
                      displayValue = `${(value as number * 100).toFixed(2)}%`;
                    } else if (metric.format === "number") {
                      displayValue = (value as number).toLocaleString();
                    } else {
                      displayValue = value as string;
                    }
                  }
                  const isInsightsColumn = metric.key === "Insights";
                  return (
                    <TableCell
                      key={`${metric.key}-${campaign.Campaign_Name}`}
                      className={`min-w-[150px] max-w-[200px] overflow-hidden border-l border-b ${
                        isInsightsColumn ? "min-w-[500px]" : "truncate text-ellipsis"
                      }`}
                      title={displayValue}
                    >
                      <div className="p-2">
                        {isInsightsColumn ? (
                          <p
                            className={`text-muted-foreground whitespace-normal text-left text-xs ${
                              expandedRow === campaign.Campaign_Name ? "whitespace-normal" : "line-clamp-5"
                            }`}
                          >
                            {displayValue}
                          </p>
                        ) : (
                          <p className="text-muted-foreground whitespace-nowrap text-right truncate">{displayValue}</p>
                        )}
                      </div>
                    </TableCell>

                  );
                })}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
  );
};

export default CampaignTable;
