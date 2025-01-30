import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  Box,
  Grid,
  Card,
  CardHeader,
  CardContent,
  Avatar,
  Typography,
  CircularProgress,
  TextField,
  Container,
  Dialog,
  DialogTitle,
  DialogContent,
  IconButton,
  Button,
  InputAdornment
} from '@mui/material';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import CloseIcon from '@mui/icons-material/Close';
import SearchIcon from '@mui/icons-material/Search';
import _ from 'lodash';
import axios from 'axios';

// Theme Constants
const COLORS = {
  primary: '#4F46E5',
  secondary: '#3B82F6',
  success: '#059669',
  warning: '#F59E0B',
  error: '#DC2626',
  aiMetric: '#059669',
  nonAiMetric: '#DC2626',
  lightBg: '#F9FAFB',
  darkText: '#111827',
  cardGradient: 'linear-gradient(135deg, #4F46E5 0%, #818CF8 100%)',
  cardHoverGradient: 'linear-gradient(135deg, #4338CA 0%, #6366F1 100%)',
  aiLine: '#059669',
  nonAiLine: '#DC2626',
  cardBg: '#FFFFFF',
  border: '#E5E7EB',
};


const getAverage = (arr, field) => {
  if (!arr || arr.length === 0) return null;
  return _.meanBy(arr, field) || 0;
};


const formatPercentage = (value) => {
  if (value === null) return 'N/A';
  if (!value && value !== 0) return '0.0%';
  return `${Number(value).toFixed(1)}%`;
};

const safeNumberFormat = (value, decimals = 1) => {
  const num = parseFloat(value);
  return isNaN(num) ? '0.0' : num.toFixed(decimals);
};
const calculatePerformanceScore = (aiCsat, aiUsagePercentage) => {
  // Weight factors can be adjusted based on importance
  const csatWeight = 0.6;  // 60% weight to CSAT
  const aiUsageWeight = 0.4;  // 40% weight to AI usage

  // Normalize scores to 0-100 scale
  const normalizedCsat = aiCsat || 0;  // CSAT is already 0-100
  const normalizedAiUsage = aiUsagePercentage || 0;  // AI usage is already 0-100

  // Calculate weighted score
  return (normalizedCsat * csatWeight) + (normalizedAiUsage * aiUsageWeight);
};


// Convert time string to minutes for chart data
const convertTimeToMinutes = (timeStr) => {
  if (!timeStr) return 0;
  try {
    const [mins, secs] = timeStr.split(':').map(Number);
    return mins + (secs / 60);
  } catch {
    return 0;
  }
};

// Base Components
const CustomCard = ({ children, title, elevation = 0 }) => (
  <Card
    elevation={elevation}
    sx={{
      height: '100%',
      borderRadius: '12px',
      overflow: 'hidden',
      transition: 'all 0.2s ease-in-out',
      backgroundColor: COLORS.cardBg,
      border: `1px solid ${COLORS.border}`,
      '&:hover': {
        transform: 'translateY(-4px)',
        boxShadow: '0 12px 24px -8px rgba(0, 0, 0, 0.12)',
      },
    }}
  >
    <CardHeader
      sx={{
        background: COLORS.cardGradient,
        p: 2.5,
        '& .MuiCardHeader-title': {
          color: 'white',
          fontSize: '1rem',
          fontWeight: 600,
          letterSpacing: '0.025em',
        }
      }}
      title={title}
    />
    <CardContent sx={{ p: 3 }}>
      {children}
    </CardContent>
  </Card>
);

const ComparisonMetricCard = ({ title, aiValue, nonAiValue, aiLabel = 'With AI', nonAiLabel = 'Without AI' }) => (
  <Card sx={{
    p: 3,
    borderRadius: '12px',
    backgroundColor: COLORS.cardBg,
    border: `1px solid ${COLORS.border}`,
    transition: 'transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out',
    '&:hover': {
      transform: 'translateY(-4px)',
      boxShadow: '0 12px 24px -8px rgba(0, 0, 0, 0.12)'
    }
  }}>
    <Typography
      variant="subtitle2"
      sx={{
        color: 'text.secondary',
        mb: 2,
        fontWeight: 500,
        fontSize: '0.875rem'
      }}>
      {title}
    </Typography>
    <Grid container spacing={3}>
      <Grid item xs={6}>
        <Typography variant="body2" sx={{
          color: COLORS.aiMetric,
          fontWeight: 600,
          mb: 1
        }}>
          {aiLabel}
        </Typography>
        <Typography variant="h5" sx={{
          color: COLORS.aiMetric,
          fontWeight: 700,
          fontSize: '1.5rem'
        }}>
          {aiValue === null ? 'N/A' : formatPercentage(aiValue)}
        </Typography>
      </Grid>
      <Grid item xs={6}>
        <Typography variant="body2" sx={{
          color: COLORS.nonAiMetric,
          fontWeight: 600,
          mb: 1
        }}>
          {nonAiLabel}
        </Typography>
        <Typography variant="h5" sx={{
          color: COLORS.nonAiMetric,
          fontWeight: 700,
          fontSize: '1.5rem'
        }}>
          {formatPercentage(nonAiValue)}
        </Typography>
      </Grid>
    </Grid>
  </Card>
);

const MetricCard = ({ title, value, color, gradient }) => (
  <Card sx={{
    p: 3,
    borderRadius: '12px',
    backgroundColor: COLORS.cardBg,
    border: `1px solid ${COLORS.border}`,
    transition: 'all 0.2s ease-in-out',
    minHeight: '80px',
    width: '80%', // Ensure card takes full width
    overflow: 'visible', // Prevent text cutoff
    '&:hover': {
      transform: 'translateY(-4px)',
      boxShadow: '0 8px 16px -4px rgba(0, 0, 0, 0.1)'
    }
  }}>
    <Typography variant="subtitle2" sx={{
      color: 'text.secondary',
      mb: 1,
      fontWeight: 500
    }}>
      {title}
    </Typography>
    <Typography variant="h3" sx={{
      fontWeight: 700,
      background: gradient || `linear-gradient(135deg, ${color} 0%, ${color} 100%)`,
      WebkitBackgroundClip: 'text',
      WebkitTextFillColor: 'transparent'
    }}>
      {value}
    </Typography>
  </Card>
);

// Main Dashboard Component
const AgentDashboard = ({ dateRange }) => {
  // States
  const [data, setData] = useState({
    agents: [],
    overallMetrics: {
      aiMetrics: {
        csat: 0,
        asat: 0,
        fcr: 0,
        nps: 0,
        aht: '0:00'
      },
      nonAiMetrics: {
        csat: 0,
        asat: 0,
        fcr: 0,
        nps: 0,
        aht: '0:00'
      },
      aiUsagePercentage: 0,
      handleTimeData: []
    }
  });
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedAgent, setSelectedAgent] = useState(null);
  const [detailsOpen, setDetailsOpen] = useState(false);
  const [error, setError] = useState(null);

  // Calculate AHT helper
  const calculateAHT = (durations) => {
    if (!durations || !durations.length) return '0:00';

    const totalSeconds = durations.reduce((sum, duration) => {
      if (!duration) return sum;
      try {
        const [mins, secs] = duration.split(':').map(str => {
          const num = parseInt(str, 10);
          return isNaN(num) ? 0 : num;
        });
        return sum + (mins * 60) + (secs || 0);
      } catch (err) {
        console.error('Error processing duration:', duration);
        return sum;
      }
    }, 0);


    const avgSeconds = Math.round(totalSeconds / durations.length);
    const mins = Math.floor(avgSeconds / 60);
    const secs = avgSeconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };
  // Data processing logic
  // Update the processData function in AgentDashboard component
  const processData = useCallback((rawData) => {
    try {
      // Validate and clean data
      const validData = rawData.map(item => ({
        name: item['Owner: Full Name'] || 'Unknown',
        status: item['Status'],
        duration: item['Chat Duration'] || '0:00',
        createdDate: item['Created Date'],
        aiAssisted: item['AIAssisted'] === 'Yes', // Updated to match new API
        fcr: parseFloat(item['FCR']) || 0,
        csat: parseFloat(item['CSAT']) || 0,
        asat: parseFloat(item['ASAT']) || 0,
        nps: parseFloat(item['NPS']) || 0
      })).filter(item => item.name !== 'Unknown');

      // Group by agent name
      const byAgent = _.groupBy(validData, 'name');

      // Process each agent's data
      // In the processData function, we need to modify this part:
      const agents = Object.entries(byAgent).map(([name, tickets]) => {
        const aiTickets = tickets.filter(t => t.aiAssisted);
        const nonAiTickets = tickets.filter(t => !t.aiAssisted);
        const hasAiTickets = aiTickets.length > 0;

        // Calculate the performance score
        const aiCsat = hasAiTickets ? getAverage(aiTickets, 'csat') : 0;
        const aiUsagePercentage = tickets.length ? (aiTickets.length / tickets.length) * 100 : 0;
        const performanceScore = calculatePerformanceScore(aiCsat, aiUsagePercentage);


        return {
          name,
          metrics: {
            ai: {
              // Only calculate AI metrics if there are AI tickets
              csat: hasAiTickets ? getAverage(aiTickets, 'csat') : null,
              asat: hasAiTickets ? getAverage(aiTickets, 'asat') : null,
              fcr: hasAiTickets ? getAverage(aiTickets, 'fcr') : null,
              nps: hasAiTickets ? getAverage(aiTickets, 'nps') : null,
              aht: hasAiTickets ? calculateAHT(aiTickets.map(t => t.duration)) : 'N/A'
            },
            nonAi: {
              csat: getAverage(nonAiTickets, 'csat') || 0,
              asat: getAverage(nonAiTickets, 'asat') || 0,
              fcr: getAverage(nonAiTickets, 'fcr') || 0,
              nps: getAverage(nonAiTickets, 'nps') || 0,
              aht: calculateAHT(nonAiTickets.map(t => t.duration))
            }
          },
          aiUsagePercentage,
          totalTickets: tickets.length,
          performanceScore
        };
      });

      // Calculate overall metrics
      const allAiTickets = validData.filter(t => t.aiAssisted);
      const allNonAiTickets = validData.filter(t => !t.aiAssisted);

      // Process handle time data by date
      const handleTimeData = Object.entries(_.groupBy(validData, item =>
        new Date(item.createdDate).toISOString().split('T')[0]
      )).map(([date, tickets]) => {
        const dayAiTickets = tickets.filter(t => t.aiAssisted);
        const dayNonAiTickets = tickets.filter(t => !t.aiAssisted);

        return {
          date,
          aiAHT: convertTimeToMinutes(calculateAHT(dayAiTickets.map(t => t.duration))),
          nonAiAHT: convertTimeToMinutes(calculateAHT(dayNonAiTickets.map(t => t.duration)))
        };
      });

      // Calculate overall metrics using the first occurrence of metrics for each agent
      const uniqueAgentMetrics = _.uniqBy(validData, 'name');
      const overallMetrics = {
        aiMetrics: {
          csat: _.meanBy(uniqueAgentMetrics, 'csat') || 0,
          asat: _.meanBy(uniqueAgentMetrics, 'asat') || 0,
          fcr: _.meanBy(uniqueAgentMetrics, 'fcr') || 0,
          nps: _.meanBy(uniqueAgentMetrics, 'nps') || 0,
          aht: calculateAHT(allAiTickets.map(t => t.duration))
        },
        nonAiMetrics: {
          csat: _.meanBy(uniqueAgentMetrics, 'csat') || 0,
          asat: _.meanBy(uniqueAgentMetrics, 'asat') || 0,
          fcr: _.meanBy(uniqueAgentMetrics, 'fcr') || 0,
          nps: _.meanBy(uniqueAgentMetrics, 'nps') || 0,
          aht: calculateAHT(allNonAiTickets.map(t => t.duration))
        },
        aiUsagePercentage: validData.length ? (allAiTickets.length / validData.length) * 100 : 0,
        handleTimeData: _.sortBy(handleTimeData, 'date')
      };

      // Sort agents by performance score and update state
      const sortedAgents = _.orderBy(agents, ['performanceScore'], ['desc']);
      setData({
        agents: sortedAgents,
        overallMetrics
      });
      setLoading(false);

    } catch (err) {
      console.error('Data processing error:', err);
      setError(err.message);
      setLoading(false);
    }
  }, []);


  // Filtered agents computation
  const filteredAgents = useMemo(() => {
    if (!searchTerm.trim()) {
      // Show top 3 by performance score
      return data.agents.slice(0, 3);
    }
    return data.agents.filter(agent =>
      agent.name.toLowerCase().includes(searchTerm.toLowerCase())
    );
  }, [data.agents, searchTerm]);

  // Data fetching
  useEffect(() => {
    const fetchData = async () => {
      if (!dateRange) return;
      setLoading(true);
      try {
        const response = await axios.get('http://localhost:5000/api/agents-data', {
          params: {
            from: dateRange.fromDate,
            to: dateRange.toDate
          }
        });
        console.log('Raw data from API:', response.data); // Debug log
        processData(response.data);
      } catch (err) {
        console.error('Fetch error:', err);
        setError(err.message);
        setLoading(false);
      }
    };

    fetchData();
  }, [dateRange, processData]);

  if (loading) {
    return (
      <Box sx={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100vh',
        background: COLORS.lightBg,
      }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100vh',
        color: COLORS.error,
        background: COLORS.lightBg,
      }}>
        <Typography variant="h6">Error: {error}</Typography>
      </Box>
    );
  }

  return (
    <Container maxWidth="xl" sx={{ py: 4, backgroundColor: COLORS.lightBg }}>
      <Typography variant="h4" sx={{
        fontWeight: 600,
        color: COLORS.darkText,
        mb: 3,
        fontSize: { xs: '1.75rem', md: '2rem' }
      }}>
        Agent Performance Dashboard
      </Typography>
      {/* Search Bar */}
      <TextField
        fullWidth
        variant="outlined"
        placeholder="Search agents..."
        value={searchTerm}
        onChange={(e) => setSearchTerm(e.target.value)}
        sx={{
          mb: 4,
          maxWidth: 400,
          '& .MuiOutlinedInput-root': {
            borderRadius: '12px',
            backgroundColor: COLORS.cardBg,
            boxShadow: '0 2px 4px rgba(0, 0, 0, 0.05)',
            border: `1px solid ${COLORS.border}`,
            '&:hover': {
              boxShadow: '0 4px 8px rgba(0, 0, 0, 0.1)',
            }
          }
        }}
        InputProps={{
          startAdornment: (
            <InputAdornment position="start">
              <SearchIcon />
            </InputAdornment>
          ),
        }}
      />
      <Grid container spacing={4} sx={{ mb: 6 }}>
        <Grid item xs={12} md={9}>
          <CustomCard title="Handle Time Trends">
            <Box sx={{
              height: 450,
              width: '100%',
              p: 2,
              bgcolor: COLORS.cardBg,
            }}>
              <ResponsiveContainer>
                <LineChart
                  data={data.overallMetrics.handleTimeData}
                  margin={{ top: 20, right: 30, left: 20, bottom: 60 }} // Increased bottom margin
                >
                  <XAxis
                    dataKey="date"
                    tickFormatter={(value) => {
                      const date = new Date(value);
                      return date.toLocaleDateString('en-US', {
                        month: 'long',
                        day: 'numeric'
                      });
                    }}
                    stroke="#64748B"
                    tick={{
                      fill: '#64748B',
                      fontSize: '0.75rem'
                    }}
                    angle={-45} //  angle for better readability
                    textAnchor="end"
                    height={70} // height for X-axis
                    tickMargin={15} // tick margin
                    interval={0}
                  />
                  <YAxis
                    tickFormatter={(value) => {
                      const mins = Math.floor(value);
                      const secs = Math.round((value % 1) * 60);
                      return `${mins}:${secs.toString().padStart(2, '0')}`;
                    }}
                    label={{
                      value: 'Handle Time (MM:SS)',
                      angle: -90,
                      position: 'insideLeft',
                      style: {
                        textAnchor: 'middle',
                        fill: '#64748B',
                        fontSize: '0.875rem'
                      }
                    }}
                    stroke="#64748B"
                    tick={{
                      fontSize: '0.75rem',
                      fill: '#64748B'
                    }}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: COLORS.cardBg,
                      border: `1px solid ${COLORS.border}`,
                      borderRadius: '8px',
                      boxShadow: '0 4px 12px rgba(0, 0, 0, 0.1)',
                      padding: '12px'
                    }}
                    labelFormatter={(value) => {
                      const date = new Date(value);
                      return date.toLocaleDateString('en-US', {
                        weekday: 'long',
                        month: 'long',
                        day: 'numeric',
                        year: 'numeric'
                      });
                    }}
                    formatter={(value, name) => {
                      const mins = Math.floor(value);
                      const secs = Math.round((value % 1) * 60);
                      return [`${mins}:${secs.toString().padStart(2, '0')}`, name === 'aiAHT' ? 'AI Handle Time' : 'Non-AI Handle Time'];
                    }}
                  />
                  <Legend
                    wrapperStyle={{
                      paddingTop: '20px',
                      fontSize: '0.875rem'
                    }}
                  />
                  <Line
                    type="monotone"
                    dataKey="aiAHT"
                    stroke={COLORS.aiLine}
                    name="AI Handle Time"
                    strokeWidth={2}
                    dot={{ r: 3, strokeWidth: 2, fill: COLORS.cardBg }}
                    activeDot={{ r: 5, strokeWidth: 2 }}
                  />
                  <Line
                    type="monotone"
                    dataKey="nonAiAHT"
                    stroke={COLORS.nonAiLine}
                    name="Non-AI Handle Time"
                    strokeWidth={2}
                    dot={{ r: 3, strokeWidth: 2, fill: COLORS.cardBg }}
                    activeDot={{ r: 5, strokeWidth: 2 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </Box>
          </CustomCard>
        </Grid>

        {/* Metrics Cards */}
        <Grid item xs={12} md={3}>
          <Grid container spacing={2} direction="row">  {/* row direction */}
            <Grid item xs={6} md={12}>
              <MetricCard
                title="Overall CSAT"
                value={`${safeNumberFormat((data.overallMetrics.aiMetrics.csat + data.overallMetrics.nonAiMetrics.csat) / 2)}%`}
                color={COLORS.success}
                gradient={`linear-gradient(135deg, ${COLORS.success} 0%, #34D399 100%)`}
                sx={{ width: '100%' }}
              />
            </Grid>
            <Grid item xs={6} md={12}>
              <MetricCard
                title="Overall ASAT"
                value={`${safeNumberFormat((data.overallMetrics.aiMetrics.asat + data.overallMetrics.nonAiMetrics.asat) / 2)}%`}
                color={COLORS.warning}
                gradient={`linear-gradient(135deg, ${COLORS.warning} 0%, #FBBF24 100%)`}
              />
            </Grid>
            <Grid item xs={6} md={12}>
              <MetricCard
                title="Overall FCR"
                value={`${safeNumberFormat((data.overallMetrics.aiMetrics.fcr + data.overallMetrics.nonAiMetrics.fcr) / 2)}%`}
                color={COLORS.primary}
                gradient={`linear-gradient(135deg, ${COLORS.primary} 0%, #6366F1 100%)`}
              />
            </Grid>
            <Grid item xs={6} md={12}>
              <MetricCard
                title="Overall NPS"
                value={`${safeNumberFormat((data.overallMetrics.aiMetrics.nps + data.overallMetrics.nonAiMetrics.nps) / 2)}%`}
                color={COLORS.secondary}
                gradient={`linear-gradient(135deg, ${COLORS.secondary} 0%, #93C5FD 100%)`}
              />
            </Grid>
          </Grid>
        </Grid>
      </Grid>

      {/* Agent List */}
      <Typography variant="h5" sx={{ mb: 3 }}>
        {searchTerm ? 'Search Results' : 'Top Performing Agents'}
      </Typography>

      {/* Agent Cards */}
      <Grid container spacing={3}>
        {filteredAgents.map((agent, index) => (
          <Grid item xs={12} sm={6} md={4} key={agent.name}>
            <Card sx={{
              height: '100%',
              borderRadius: '12px',
              bgcolor: COLORS.cardBg,
              border: `1px solid ${COLORS.border}`,
              transition: 'all 0.2s ease-in-out',
              '&:hover': {
                transform: 'translateY(-4px)',
                boxShadow: '0 12px 24px -8px rgba(0, 0, 0, 0.12)',
              }
            }}>
              <CardContent sx={{ p: 3 }}>
                {/* Agent Header */}
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                  <Avatar sx={{
                    bgcolor: index === 0 ? COLORS.warning : COLORS.primary,
                    width: 56,
                    height: 56,
                    mr: 2,
                  }}>
                    {agent.name[0]}
                  </Avatar>
                  <Box>
                    <Typography variant="h6" sx={{ fontWeight: 600 }}>
                      {agent.name}
                    </Typography>
                    {!searchTerm && (
                      <Typography variant="body2" color="text.secondary">
                        Performance Score: {agent.performanceScore.toFixed(1)}
                      </Typography>
                    )}
                  </Box>
                </Box>



                {/* AI Usage Info */}
                <Box sx={{
                  p: 2,
                  bgcolor: COLORS.lightBg,
                  borderRadius: '12px',
                  mb: 3
                }}>
                  <Grid container spacing={2}>
                    <Grid item xs={6}>
                      <Typography variant="caption" color="text.secondary">
                        AI Usage
                      </Typography>
                      <Typography variant="h6" sx={{ color: COLORS.aiMetric, fontWeight: 600 }}>
                        {formatPercentage(agent.aiUsagePercentage)}
                      </Typography>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="caption" color="text.secondary">
                        Handle Time
                      </Typography>
                      <Typography variant="body2" sx={{ color: COLORS.aiMetric }}>
                        AI: {agent.metrics.ai.aht}
                      </Typography>
                      <Typography variant="body2" sx={{ color: COLORS.nonAiMetric }}>
                        Non-AI: {agent.metrics.nonAi.aht}
                      </Typography>
                    </Grid>
                  </Grid>
                </Box>

                {/* Details Button */}
                <Button
                  fullWidth
                  variant="contained"
                  onClick={() => {
                    setSelectedAgent(agent);
                    setDetailsOpen(true);
                  }}
                  sx={{
                    background: COLORS.cardGradient,
                    borderRadius: '12px',
                    textTransform: 'none',
                    py: 1.5,
                    fontWeight: 600,
                    '&:hover': {
                      background: COLORS.cardHoverGradient,
                    }
                  }}
                >
                  View Details
                </Button>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Agent Details Dialog */}
      <Dialog
        open={detailsOpen}
        onClose={() => {
          setDetailsOpen(false);
          setSelectedAgent(null);
        }}
        maxWidth="lg"
        fullWidth
        PaperProps={{
          sx: {
            borderRadius: '16px',
            bgcolor: COLORS.lightBg,
            overflow: 'hidden',
            boxShadow: '0 24px 48px -12px rgba(0, 0, 0, 0.18)'
          }
        }}
      >
        {selectedAgent && (
          <>
            <DialogTitle sx={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              background: COLORS.cardGradient,
              color: 'white',
              py: 3,
              px: 4,
            }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <Avatar sx={{
                  bgcolor: 'white',
                  color: COLORS.primary,
                  width: 56,
                  height: 56,
                }}>
                  {selectedAgent.name[0]}
                </Avatar>
                <Box>
                  <Typography variant="h5" sx={{ fontWeight: 600 }}>
                    {selectedAgent.name}
                  </Typography>
                  <Typography variant="subtitle1">
                    Performance Details
                  </Typography>
                </Box>
              </Box>
              <IconButton
                onClick={() => setDetailsOpen(false)}
                sx={{ color: 'white' }}
              >
                <CloseIcon />
              </IconButton>
            </DialogTitle>

            <DialogContent sx={{ p: 4 }}>
              <Grid container spacing={3}>
                {/* Metrics */}
                <Grid item xs={12} md={3}>
                  <ComparisonMetricCard
                    title="CSAT Score"
                    aiValue={selectedAgent.metrics.ai.csat}
                    nonAiValue={selectedAgent.metrics.nonAi.csat}
                  />
                </Grid>
                <Grid item xs={12} md={3}>
                  <ComparisonMetricCard
                    title="ASAT Score"
                    aiValue={selectedAgent.metrics.ai.asat}
                    nonAiValue={selectedAgent.metrics.nonAi.asat}
                  />
                </Grid>
                <Grid item xs={12} md={3}>
                  <ComparisonMetricCard
                    title="FCR Rate"
                    aiValue={selectedAgent.metrics.ai.fcr}
                    nonAiValue={selectedAgent.metrics.nonAi.fcr}
                  />
                </Grid>
                <Grid item xs={12} md={3}>
                  <ComparisonMetricCard
                    title="NPS Score"
                    aiValue={selectedAgent.metrics.ai.nps}
                    nonAiValue={selectedAgent.metrics.nonAi.nps}
                  />
                </Grid>

                {/* Analysis */}
                <Grid item xs={12}>
                  <Card sx={{ p: 3 }}>
                    <Typography variant="h6" gutterBottom>
                      Performance Analysis
                    </Typography>
                    <Grid container spacing={3}>
                      <Grid item xs={12} md={6}>
                        <Box>
                          <Typography variant="subtitle2" color="text.secondary">
                            AI Usage Impact
                          </Typography>
                          <Typography variant="body1">
                            {selectedAgent.name} utilizes AI assistance in {formatPercentage(selectedAgent.aiUsagePercentage)} of tickets,
                            with an average handle time of {selectedAgent.metrics.ai.aht} for AI-assisted tickets compared to
                            {selectedAgent.metrics.nonAi.aht} for non-AI tickets.
                          </Typography>
                        </Box>
                      </Grid>
                      <Grid item xs={12} md={6}>
                        <Box>
                          <Typography variant="subtitle2" color="text.secondary">
                            Customer Satisfaction
                          </Typography>
                          <Typography variant="body1">
                            Maintains a CSAT score of {formatPercentage(selectedAgent.metrics.ai.csat)} with AI assistance,
                            and FCR rate of {formatPercentage(selectedAgent.metrics.ai.fcr)}.
                          </Typography>
                        </Box>
                      </Grid>
                    </Grid>
                  </Card>
                </Grid>
              </Grid>
            </DialogContent>
          </>
        )}
      </Dialog>
    </Container>
  );
};

export default AgentDashboard;