// NodeMetrics.tsx - Highly simplified version with better spacing
import React from 'react';
import { NodeType } from './type';

interface NodeMetricsProps {
    nodeType: NodeType;
    metrics: any;
    isActive: boolean;
    isComplete: boolean;
}

const NodeMetrics: React.FC<NodeMetricsProps> = ({ nodeType, metrics, isActive, isComplete }) => {
    // Different metrics based on node type
    const getMetricsByType = () => {
        switch (nodeType) {
            case 'RAG':
                return [
                    { name: 'R', value: metrics.relevance || 95, unit: '%' },
                    { name: 'C', value: metrics.coherence || 93, unit: '%' },
                    { name: 'A', value: metrics.accuracy || 90, unit: '%' }
                ];
            case 'Database':
                return [
                    { name: 'Time', value: metrics.queryTime || 42, unit: 'ms' },
                    { name: 'Rows', value: metrics.records || 1240, unit: '' },
                    { name: 'Hit', value: metrics.cacheHit || 78, unit: '%' }
                ];
            case 'Web Search':
                return [
                    { name: 'Src', value: metrics.sources || 8, unit: '' },
                    { name: 'Fresh', value: metrics.freshness || 96, unit: '%' },
                    { name: 'Rel', value: metrics.relevance || 92, unit: '%' }
                ];
            case 'LLM':
                return [
                    { name: 'Tokens', value: metrics.tokens || 845, unit: '' },
                    { name: 'Time', value: metrics.latency || 320, unit: 'ms' },
                    { name: 'PPL', value: metrics.perplexity || 3.4, unit: '' }
                ];
            case 'Q&A':
                return [
                    { name: 'P', value: metrics.precision || 94, unit: '%' },
                    { name: 'R', value: metrics.recall || 87, unit: '%' },
                    { name: 'F1', value: metrics.f1Score || 95, unit: '%' }
                ];
            case 'Code Execution':
                return [
                    { name: 'Time', value: metrics.runtime || 62, unit: 'ms' },
                    { name: 'Mem', value: metrics.memory || 24.6, unit: 'MB' },
                    { name: 'Pass', value: metrics.success || 98, unit: '%' }
                ];
            default:
                return [
                    { name: 'Time', value: metrics.completionTime || 85, unit: 'ms' },
                    { name: 'Succ', value: metrics.successRate || 95, unit: '%' },
                    { name: 'Err', value: metrics.errorRate || 1, unit: '%' }
                ];
        }
    };

    // Get color scheme based on node type
    const getColorScheme = () => {
        switch (nodeType) {
            case 'Router':
            case 'RAG':
            case 'Q&A':
            case 'Summarizer':
                return {
                    bgActive: 'bg-indigo-500',
                    bgComplete: 'bg-indigo-100',
                    textActive: 'text-white',
                    textComplete: 'text-indigo-700',
                    border: 'border-indigo-200'
                };
            case 'Database':
            case 'Web Search':
            case 'Compute':
            case 'File Reader':
                return {
                    bgActive: 'bg-emerald-500',
                    bgComplete: 'bg-emerald-100',
                    textActive: 'text-white',
                    textComplete: 'text-emerald-700',
                    border: 'border-emerald-200'
                };
            case 'Code Execution':
            case 'API Connector':
            case 'LLM':
            case 'Vector Store':
                return {
                    bgActive: 'bg-amber-500',
                    bgComplete: 'bg-amber-100',
                    textActive: 'text-white',
                    textComplete: 'text-amber-700',
                    border: 'border-amber-200'
                };
            default:
                return {
                    bgActive: 'bg-gray-500',
                    bgComplete: 'bg-gray-100',
                    textActive: 'text-white',
                    textComplete: 'text-gray-700',
                    border: 'border-gray-200'
                };
        }
    };

    const colors = getColorScheme();
    const displayMetrics = getMetricsByType();
    const animationClass = isActive ? 'animate-pulse' : '';
    const bgClass = isActive ? colors.bgActive : isComplete ? colors.bgComplete : 'bg-gray-50';
    const textClass = isActive ? colors.textActive : isComplete ? colors.textComplete : 'text-gray-600';

    return (
        <div className={`grid grid-cols-3 w-full text-center py-1.5 ${animationClass}`}>
            {displayMetrics.map((metric, index) => (
                <div key={index} className="flex flex-col items-center px-1">
                    <div className={`text-xs font-medium text-gray-500 mb-0.5`}>{metric.name}</div>
                    <div className={`text-sm font-bold text-gray-700`}>
                        {typeof metric.value === 'number' ?
                            (metric.value % 1 === 0 ? metric.value : metric.value.toFixed(1)) :
                            metric.value}
                        {metric.unit}
                    </div>
                </div>
            ))}
        </div>
    );
};

export default NodeMetrics;