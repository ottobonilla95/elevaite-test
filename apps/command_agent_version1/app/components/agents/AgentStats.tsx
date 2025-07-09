"use client";

import React from "react";
import { useAgents } from "../../ui/contexts/AgentsContext";
import { Users, Activity, CheckCircle, Clock } from "lucide-react";

interface AgentStatsProps {
  className?: string;
}

function AgentStats({ className = "" }: AgentStatsProps): JSX.Element {
  const {
    agents,
    isLoading,
    error,
    getAgentCount,
    getDeployedAgents,
    getActiveAgents,
    getAgentsByType,
    lastUpdated
  } = useAgents();

  if (isLoading && agents.length === 0) {
    return (
      <div className={`bg-white rounded-lg border border-gray-200 p-4 ${className}`}>
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="grid grid-cols-2 gap-4">
            <div className="h-16 bg-gray-200 rounded"></div>
            <div className="h-16 bg-gray-200 rounded"></div>
            <div className="h-16 bg-gray-200 rounded"></div>
            <div className="h-16 bg-gray-200 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`bg-white rounded-lg border border-red-200 p-4 ${className}`}>
        <div className="text-red-600 text-sm">
          <p className="font-medium">Error loading agent statistics</p>
          <p className="text-xs mt-1">{error}</p>
        </div>
      </div>
    );
  }

  const totalAgents = getAgentCount();
  const deployedAgents = getDeployedAgents();
  const activeAgents = getActiveAgents();
  const routerAgents = getAgentsByType('router');

  const stats = [
    {
      label: "Total Agents",
      value: totalAgents,
      icon: <Users size={16} />,
      color: "text-blue-600",
      bgColor: "bg-blue-50"
    },
    {
      label: "Deployed",
      value: deployedAgents.length,
      icon: <CheckCircle size={16} />,
      color: "text-green-600",
      bgColor: "bg-green-50"
    },
    {
      label: "Active",
      value: activeAgents.length,
      icon: <Activity size={16} />,
      color: "text-orange-600",
      bgColor: "bg-orange-50"
    },
    {
      label: "Router Agents",
      value: routerAgents.length,
      icon: <Clock size={16} />,
      color: "text-purple-600",
      bgColor: "bg-purple-50"
    }
  ];

  return (
    <div className={`bg-white rounded-lg border border-gray-200 p-4 ${className}`}>
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-medium text-gray-900">Agent Statistics</h3>
        {lastUpdated ? <span className="text-xs text-gray-500">
          Updated {lastUpdated.toLocaleTimeString()}
        </span> : null}
      </div>

      <div className="grid grid-cols-2 gap-3">
        {stats.map((stat, index) => (
          <div
            key={index}
            className={`${stat.bgColor} rounded-lg p-3 flex items-center space-x-2`}
          >
            <div className={stat.color}>
              {stat.icon}
            </div>
            <div>
              <p className="text-xs text-gray-600">{stat.label}</p>
              <p className={`text-lg font-semibold ${stat.color}`}>
                {stat.value}
              </p>
            </div>
          </div>
        ))}
      </div>

      {totalAgents > 0 && (
        <div className="mt-4 pt-3 border-t border-gray-100">
          <div className="flex justify-between text-xs text-gray-500">
            <span>Deployment Rate</span>
            <span>{Math.round((deployedAgents.length / totalAgents) * 100)}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-1.5 mt-1">
            <div
              className="bg-green-600 h-1.5 rounded-full transition-all duration-300"
              style={{ width: `${(deployedAgents.length / totalAgents) * 100}%` }}
            />
          </div>
        </div>
      )}
    </div>
  );
}

export default AgentStats;
