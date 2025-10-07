
// ============ CORE SUMMARY METRICS ============

export interface SummaryMetrics {
    total_srs: number;
    avg_requests_per_day: number;
    recent_avg_requests_per_day: number;
    avg_travel_time: number;
    avg_travel_time_formatted: string;
    avg_resolution_time: number;
    top_machine_type: string;
    total_parts_cost: number;
    unique_parts: number;
    top_machine_model: string;
    date_range: {
        start: string | null;
        end: string | null;
    };
}

export interface EnhancedSummaryMetrics extends SummaryMetrics {
    total_queries: number;
    avg_queries_per_day: number;
    query_trends: TrendData[];
    query_growth_rate?: number;
    total_sessions?: number;
    avg_queries_per_session?: number;
}

// ============ QUERY ANALYTICS TYPES ============

export interface QueryAnalyticsMetrics {
    total_sessions: number;
    total_queries: number;
    queries_per_session: number;
    repeat_queries_percentage: number;
    accuracy_percentage: number;
    avg_response_time_seconds: number;
    avg_queries_per_day: number;
    thumbs_up_percentage: number;
    thumbs_down_percentage: number;
    feedback_distribution: Array<{
        type: string;
        count: number;
        percentage: number;
    }>;
    _source: string;
}

export interface QueryHourlyUsage {
    hour: string;
    queries: number;
}

export interface QueryFeedbackData {
    query: string;
    response: string;
    timestamp: string;
    user: string;
    feedback: string;
    session_id: string;
}

export interface QueryExportData {
    total_records: number;
    data: Array<{
        'Query ID': string;
        'Session ID': string;
        'Request': string;
        'Response': string;
        'Request Time': string;
        'Response Time': string;
        'User ID': string;
        'Vote': string;
        'Feedback': string;
        'SR Ticket': string;
    }>;
    note?: string;
}

export interface QueryConnectionTest {
    status: string;
    message: string;
    total_queries?: number;
}

export interface QueryCategoryData {
    category: string;
    count: number;
    percentage: number;
    color?: string;
}

export interface UnresolvedQuery {
    text: string;
    count: number;
    percentage: string;
    feedback: 'Mostly 👎' | 'Mostly 👍' | 'Mixed' | 'Neutral';
    botConfidence: string;
}

export interface CustomerQueryData {
    customer_name: string;
    query_types: {
        diagnostic_codes: number;
        part_number_search: number;
        how_to_procedures: number;
        troubleshooting: number;
        general: number;
    };
}

export interface QueryTypesByCustomer {
    customers: string[];
    queryTypes: string[];
    heatmapData: number[][];
}

export interface QueryInsights {
    busyHour: string;
    quietHour: string;
    resolutionRate: number;
    userSatisfaction: number;
    peakUsagePeriod: string;
}

// ============ COMMON DATA TYPES ============

export interface TrendData {
    date: string;
    value: number;
}

export interface DistributionData {
    name: string;
    value: number;
    count?: number;
    color?: string;
}

export interface SeverityData {
    label: string;
    count: number;
    color: string;
}

// ============ CUSTOMER ANALYTICS TYPES ============

export interface CustomerData {
    customer: string;
    customerAccount?: string;
    serviceRequests: number;
    percentTotal: string;
    avgResolutionTime: string;
}

export interface CustomerProportion {
    name: string;
    value: number;
    count: number;
    color?: string;
}

export interface CustomerRequestData {
    customer: string;
    requests: number;
    color: string;
}

export interface CustomerResolutionTime {
    customer: string;
    customerAccount: string;
    avgResolutionDays: number;
    totalResolvedRequests: number;
}

export interface CustomerSeverityBreakdown {
    customer: string;
    customerAccount: string;
    severityBreakdown: Array<{
        severity: 'Critical' | 'High' | 'Medium' | 'Low' | 'Unknown';
        count: number;
        percentage: number;
        color: string;
    }>;
    totalRequests: number;
}

export interface CustomerDetailedMetrics {
    customer: string;
    customerAccount: string;
    serviceRequests: {
        total: number;
        resolved: number;
        open: number;
        resolutionRate: number;
    };
    performance: {
        avgResolutionDays: number;
    };
    resources: {
        uniquePartsUsed: number;
        totalPartsCost: number;
    };
}

export interface CustomerHeatmapData {
    customers: string[];
    machineTypes: string[];
    heatmapData: number[][];
}

export interface IssueConcentration {
    data: Array<{
        name: string;
        value: number;
        count: number;
        color: string;
    }>;
    totalTickets: number;
}

export interface CustomerTypeIssue {
    customerType: string;
    mostCommonIssue: string;
    occurnces: number;
    typesOfIssues: number;
    percentage: number;
    mostReplacedPart: string;
    partCount: number;
    partCost: number;
}

// ============ PRODUCT ANALYTICS TYPES ============

export interface PartsData {
    partNumber: string;
    description: string;
    unitCost: number;
    totalCost: number;
    count: number;
    machineType?: string;
}

export interface MachinePartsBreakdown {
    machineType: string;
    serviceRequests: number;
    totalPartsOrdered: number;
    totalPartsCost: number;
    uniquePartsCount: number;
    topParts: Array<{
        partNumber: string;
        description: string;
        count: number;
        totalCost: number;
        avgUnitCost: number;
        costPercentage?: number;
    }>;
}

export interface MachineOverviewData {
    typeDistribution: Array<{
        name: string;
        value: number;
        count: number;
        color: string;
    }>;
    topModelsByType: Array<{  // Changed from 'topModels'
        machineType: string;
        models: Array<{
            model: string;
            count: number;
        }>;
    }>;
    typeBarChart: Array<{
        label: string;
        count: number;
        color: string;
    }>;
    replacementTrend?: Array<{
        date: string;
        value: number;
    }>;
}

export interface MachineDetail {
    machine_type: string;
    service_requests: number;
    total_cost: number;
    avg_resolution_time: number;
}

// ============ ISSUE CATEGORIES TYPES ============

export interface IssueCategoryData {
    name: string;
    value: number;
    color: string;
}

export interface CategoryBarData {
    category: string;
    value: number;
}

export interface IssueStatistics {
    totalIssues: number;
    mostCommonIssue: {
        issue: string;
        count: number;
        percentage: number;
    };
    mostReplacedPart: {
        partNumber: string;
        description: string;
        count: number;
        cost: number;
    };
    resolutionRate: {
        rate: number;
        change: number;
    };
}

export interface MachineTypeIssue {
    machineType: string;
    mostCommonIssue: string;
    occurnces: number;
    typesOfIssues: number;
    percentage: number;
    mostReplacedPart: string;
    partCount: number;
}

export interface PartsIssueCorrelation {
    issue: string;
    partDescription: string;
    occurrenceCount: number;
}

export interface ReplacedPartsOverview {
    topReplacedParts: Array<{
        partNumber: string;
        description: string;
        replacementCount: number;
        totalCost: number;
        serviceRequests: number;
        machineTypes: number;
    }>;
    summary: {
        uniquePartsCount: number;
        totalCost: number;
        totalReplacements: number;
        affectedServiceRequests: number;
        percentRequiringParts: number;
    };
}

// ============ SERVICE PERFORMANCE TYPES ============

export interface ServiceMetrics {
    travel_time?: {
        total: number;
        average: number;
        formatted: string;
        value?: number;
    };
    service_time?: {
        total: number;
        average: number;
        formatted: string;
        value?: number;
    };
    resolution_time?: {
        average: number;
        formatted: string;
    };
    top_technician?: {
        name: string;
        count: number;
    };
}

export interface TechnicianPerformance {
    technician_name: string;
    service_requests: number;
    avg_resolution_time: number;
    avg_travel_time: number;
    customer_satisfaction?: number;
}

export interface RegionTravelTime {
    region: string;
    avgTravelTime: number;
    color: string;
}

export interface TimeAnalysis {
    overview?: {
        totalTime: number;
        serviceTime: number;
        travelTime: number;
    };
    byMachineType?: Array<{
        machineType: string;
        serviceTime: number;
        travelTime: number;
    }>;
    byCustomer?: Array<{
        customer: string;
        serviceTime: number;
        travelTime: number;
    }>;
}

// ============ FILTER TYPES ============

export interface DateFilters {
    start_date?: string;
    end_date?: string;
}

export interface QueryFilters extends DateFilters {
    customer?: string;
    query_type?: string;
    feedback_type?: 'thumbs_up' | 'thumbs_down' | 'no_vote';
    user_id?: string;
}

export interface CustomerFilters extends DateFilters {
    customer_account?: string;
    customer?: string;
}

export interface ProductFilters extends DateFilters {
    machine_type?: string;
    limit?: number;
}

export interface DateValidationResult {
    isValid: boolean;
    error?: string;
    validatedStart?: string;
    validatedEnd?: string;
}

// ============ API RESPONSE WRAPPERS ============

export interface ApiResponse<T> {
    success: boolean;
    data?: T;
    error?: string;
    message?: string;
    timestamp?: string;
}

export interface PaginatedResponse<T> {
    data: T[];
    pagination: {
        page: number;
        pageSize: number;
        total: number;
        totalPages: number;
        hasNext: boolean;
        hasPrev: boolean;
    };
}

// ============ COMBINED DASHBOARD TYPES ============

export interface DashboardMetrics {
    serviceRequests: SummaryMetrics;
    queryAnalytics: QueryAnalyticsMetrics;
    combinedInsights: {
        totalInteractions: number; // SRs + Queries
        digitalAdoptionRate: number; // Queries / (SRs + Queries)
        userEngagement: number;
        resolutionEfficiency: number;
    };
}

export interface UnifiedAnalytics {
    summary: EnhancedSummaryMetrics;
    trends: {
        serviceRequests: TrendData[];
        queries: TrendData[];
        combined: TrendData[];
    };
    performance: {
        serviceResolution: number;
        queryAccuracy: number;
        overallSatisfaction: number;
    };
}

// ============ COMPONENT PROPS TYPES ============

export interface TabComponentProps {
    dateFilters: DateFilters;
}

export interface QueryAnalyticsProps {
    dateFilters?: DateFilters;
    onDataLoad?: (data: QueryAnalyticsMetrics) => void;
    onError?: (error: string) => void;
}

export interface CustomerAnalyticsProps {
    dateFilters: DateFilters;
    selectedCustomer?: string;
    onCustomerSelect?: (customer: string) => void;
}

export interface ProductAnalysisProps {
    dateFilters: DateFilters;
    selectedMachineType?: string;
    onMachineTypeSelect?: (machineType: string) => void;
}

// ============ CHART DATA TYPES ============

export interface ChartDataPoint {
    name: string;
    value: number;
    color?: string;
    label?: string;
}

export interface LineChartData {
    date: string;
    value: number;
    label?: string;
}

export interface BarChartData {
    label: string;
    count: number;
    color: string;
    percentage?: number;
}

export interface PieChartData {
    name: string;
    value: number;
    count: number;
    color: string;
    percentage?: number;
}

export interface HeatmapData {
    rows: string[];
    columns: string[];
    data: number[][];
    colors?: string[][];
}

// ============ TABLE TYPES ============

export interface TableColumn<T> {
    key: keyof T;
    label: string;
    sortable?: boolean;
    render?: (value: any, item: T) => React.ReactNode;
    width?: string;
}

export interface TableProps<T> {
    data: T[];
    columns: TableColumn<T>[];
    loading?: boolean;
    pagination?: {
        page: number;
        pageSize: number;
        total: number;
        onPageChange: (page: number) => void;
        onPageSizeChange: (size: number) => void;
    };
    onSort?: (key: keyof T, direction: 'asc' | 'desc') => void;
    onRowClick?: (item: T) => void;
}

// ============ MODAL TYPES ============

export interface ModalProps {
    isOpen: boolean;
    onClose: () => void;
    title: string;
    children: React.ReactNode;
    size?: 'small' | 'medium' | 'large' | 'xlarge';
}

export interface QueryModalData {
    queries: QueryFeedbackData[];
    loading: boolean;
    error?: string;
    type: 'thumbs_up' | 'thumbs_down';
}

// ============ EXPORT TYPES ============

export interface ExportOptions {
    format: 'excel' | 'csv' | 'pdf';
    filename?: string;
    includeHeaders?: boolean;
    dateRange?: DateFilters;
}

export interface ExportResult {
    success: boolean;
    filename?: string;
    downloadUrl?: string;
    error?: string;
}

// ============ UTILITY TYPES ============

export type LoadingState = 'idle' | 'loading' | 'success' | 'error';

export type SortDirection = 'asc' | 'desc';

export type DataSource = 'real_database' | 'real_chatbot_database' | 'fallback_data' | 'sample_data';

export interface ComponentState<T> {
    data: T | null;
    loading: boolean;
    error: string | null;
    lastUpdated?: Date;
    source?: DataSource;
}

// ============ AUTHENTICATION TYPES ============

export interface User {
    id: string;
    email: string;
    name: string;
    role: 'admin' | 'user' | 'viewer';
    permissions: string[];
}

export interface Session {
    user: User;
    token: string;
    expiresAt: Date;
}

// ============ CHATBOT INTEGRATION TYPES ============

export interface ChatBotGenAI {
    model: string;
    temperature?: number;
    maxTokens?: number;
}

export interface ChatbotV {
    version: string;
    endpoint: string;
}

export interface ChatMessageResponse {
    response: string;
    confidence?: number;
    sources?: string[];
    timestamp: Date;
}

export interface SessionSummaryObject {
    sessionId: string;
    summary: string;
    queryCount: number;
    avgResponseTime: number;
    userSatisfaction?: number;
}