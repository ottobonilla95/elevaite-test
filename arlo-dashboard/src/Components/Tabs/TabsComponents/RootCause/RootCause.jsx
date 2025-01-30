import React, { useState, useEffect, useMemo } from 'react';
import {
  Box, Grid, Card, CardContent, CardHeader, Typography, LinearProgress,
  Divider, CircularProgress, Button, Table, TableBody, TableCell,
  TableContainer, TableHead, TableRow, Paper, Fade, Collapse
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis,
  Tooltip, Cell
} from 'recharts';
import _ from 'lodash';
import axios from 'axios';

const COLORS = ['#7C3AED', '#3B82F6', '#10B981', '#F59E0B', '#EF4444'];
const GRADIENTS = [
  'linear-gradient(135deg, #6366F1 0%, #7C3AED 100%)',
  'linear-gradient(135deg, #2563EB 0%, #3B82F6 100%)',
  'linear-gradient(135deg, #059669 0%, #10B981 100%)'
];

function CustomCard({ children, gradientIndex = 0 }) {
  return (
    <Card sx={{
      backgroundColor: '#fff',
      boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1)',
      borderRadius: '16px',
      overflow: 'hidden',
      transition: 'all 0.3s ease',
      '&:hover': {
        transform: 'translateY(-5px)',
        boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1)',
      },
      height: '100%',
      position: 'relative',
      '&::before': {
        content: '""',
        position: 'absolute',
        top: 0,
        left: 0,
        right: 0,
        height: '4px',
        background: GRADIENTS[gradientIndex]
      }
    }}>
      {children}
    </Card>
  );
}

function RootCause({ dateRange }) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [data, setData] = useState([]);
  const [showAll, setShowAll] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      if (!dateRange) {
        return;
      }

      try {
        const response = await axios.get(`http://localhost:5000/api/problems-data`, {
          params: {
            from: dateRange.fromDate,
            to: dateRange.toDate
          }
        });
        const responseData = response.data;
        setData(responseData);
        setLoading(false);
      } catch (error) {
        console.error('Error fetching data:', error);
        setError(error.message);
        setLoading(false);
      }
    };
    fetchData();
  }, [dateRange]);

  const processedData = useMemo(() => {
    if (!data.length) return null;

    // First, filter out Case Closed and Duplicate Case
    const filteredData = data.filter(item => {
      const rootCause = item['Root cause'].toLowerCase().trim();
      return !rootCause.includes('case closed') && !rootCause.includes('duplicate case');
    });

    const rootCauseCounts = _.groupBy(filteredData, 'Root cause');
    const cleanRootCause = (cause) => cause.split('(')[0].trim();

    const detailedIssues = Object.entries(rootCauseCounts)
      .map(([category, items]) => ({
        category: cleanRootCause(category),
        total: items.length,
        aiUsedCount: items.filter(item => item['AI Usage ID'] === 'Yes').length,
        ElevAIte: ((items.filter(item => item['AI Usage ID'] === 'Yes').length / items.length) * 100).toFixed(0),
        aht: items.some(item => !isNaN(parseFloat(item['Chat Duration']))) ?
          (_.meanBy(items, item => parseFloat(item['Chat Duration'])) || 0).toFixed(2) : 'N/A',
        subCategories: Object.entries(_.groupBy(items, 'Symptoms'))
          .map(([name, subItems]) => ({
            name,
            percentage: ((subItems.length / items.length) * 100).toFixed(0),
            count: subItems.length
          }))
          .sort((a, b) => b.count - a.count)
          .slice(0, 3)
      }))
      .sort((a, b) => b.total - a.total);

    const chartData = detailedIssues
      .slice(0, 3)
      .map(issue => ({
        name: issue.category,
        value: issue.total
      }));

    return {
      detailedIssues,
      chartData,
      topCategories: detailedIssues.slice(0, 5).map(issue => issue.category)
    };
  }, [data]);

  if (loading) return (
    <Box sx={{
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      height: '100vh',
      background: '#f9fafb'
    }}>
      <CircularProgress size={60} thickness={4} />
    </Box>
  );

  if (error) return (
    <Box sx={{
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      height: '100vh',
      background: '#f9fafb',
      color: '#ef4444'
    }}>
      Error: {error}
    </Box>
  );

  if (!processedData) return null;

  const { detailedIssues, chartData } = processedData;
  // Take top 3 issues after filtering
  const top3Issues = detailedIssues.slice(0, 3);
  const remainingIssues = detailedIssues.slice(3);

  return (
    <Box sx={{
      padding: '32px',
      background: '#f9fafb',
      minHeight: '100vh'
    }}>
      {/* Header */}
      <Typography
        variant="h4"
        sx={{
          mb: 4,
          fontWeight: 600,
          background: 'linear-gradient(to right, #1e293b, #334155)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent'
        }}
      >
        Root Cause Analysis
      </Typography>

      {/* Top 3 Root Causes */}
      <Grid container spacing={4} sx={{ mb: 6 }}>
        {top3Issues.map((issue, index) => (
          <Grid item xs={12} md={4} key={issue.category}>
            <Fade in={true} timeout={500 + index * 200}>
              <Box>
                <CustomCard gradientIndex={index}>
                  <CardHeader
                    title={issue.category}
                    sx={{
                      p: 3,
                      '& .MuiCardHeader-title': {
                        fontSize: '1.25rem',
                        fontWeight: 600,
                        color: '#1e293b'
                      }
                    }}
                  />
                  <CardContent sx={{ p: 3 }}>
                    <Grid container spacing={3}>
                      <Grid item xs={6}>
                        <Typography variant="h3" sx={{
                          fontWeight: 700,
                          color: COLORS[index],
                          textAlign: 'center'
                        }}>
                          {issue.total}
                        </Typography>
                        <Typography variant="body2" sx={{
                          color: '#64748b',
                          textAlign: 'center',
                          mt: 1
                        }}>
                          Total Cases
                        </Typography>
                      </Grid>
                      <Grid item xs={6}>
                        <Typography variant="h3" sx={{
                          fontWeight: 700,
                          color: COLORS[index],
                          textAlign: 'center'
                        }}>
                          {issue.ElevAIte}%
                        </Typography>
                        <Typography variant="body2" sx={{
                          color: '#64748b',
                          textAlign: 'center',
                          mt: 1
                        }}>
                          ElevAIte Usage Rate
                        </Typography>
                      </Grid>

                      <Grid item xs={12}>
                        <Box sx={{
                          bgcolor: '#f8fafc',
                          p: 2,
                          borderRadius: 2,
                          mt: 2
                        }}>
                          <Typography variant="h6" sx={{
                            color: '#475569',
                            mb: 1,
                            display: 'flex',
                            alignItems: 'center',
                            gap: 1
                          }}>
                            <TrendingUpIcon /> AHT: {issue.aht} min
                          </Typography>
                        </Box>
                      </Grid>
                    </Grid>

                    <Divider sx={{ my: 3 }} />

                    <Typography variant="subtitle1" sx={{
                      mb: 2,
                      color: '#475569',
                      fontWeight: 600
                    }}>
                      Top Symptoms
                    </Typography>
                    {issue.subCategories.map((sub) => (
                      <Box key={sub.name} sx={{ mb: 2 }}>
                        <Box sx={{
                          display: 'flex',
                          justifyContent: 'space-between',
                          mb: 1
                        }}>
                          <Typography variant="body2" sx={{ color: '#64748b' }}>
                            {sub.name}
                          </Typography>
                          <Typography variant="body2" sx={{
                            color: '#64748b',
                            fontWeight: 600
                          }}>
                            {sub.count} ({sub.percentage}%)
                          </Typography>
                        </Box>
                        <LinearProgress
                          variant="determinate"
                          value={parseInt(sub.percentage)}
                          sx={{
                            height: 6,
                            borderRadius: 3,
                            bgcolor: '#e2e8f0',
                            '& .MuiLinearProgress-bar': {
                              borderRadius: 3,
                              background: GRADIENTS[index]
                            }
                          }}
                        />
                      </Box>
                    ))}
                  </CardContent>
                </CustomCard>
              </Box>
            </Fade>
          </Grid>
        ))}
      </Grid>

      {/* Bar Chart */}
      <Fade in={true} timeout={1000}>
        <Card sx={{
          mb: 6,
          borderRadius: '16px',
          boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1)',
          overflow: 'hidden'
        }}>
          <CardHeader
            title="Trend Analysis"
            sx={{
              p: 3,
              background: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
              '& .MuiCardHeader-title': {
                color: '#fff',
                fontSize: '1.25rem',
                fontWeight: 600
              }
            }}
          />
          <CardContent sx={{ p: 3 }}>
            <ResponsiveContainer width="100%" height={400}>
              <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 70 }}>
                <XAxis
                  dataKey="name"
                  tick={{
                    fill: '#1e293b',
                    fontSize: 12,
                    width: 200,
                    textAnchor: 'middle',
                    dy: 10,
                    dx: -10
                  }}
                  height={120}
                  label={{
                    value: 'Root Causes',
                    position: 'bottom',
                    offset: 0,
                    fill: '#1e293b',
                    fontSize: 14
                  }}
                  interval={0}
                />
                <YAxis
                  tick={{ fill: '#1e293b' }}
                  label={{
                    value: 'Number of Cases',
                    angle: -90,
                    position: 'left',
                    offset: 0,
                    fill: '#1e293b',
                    fontSize: 14
                  }}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#fff',
                    border: 'none',
                    borderRadius: '8px',
                    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                  }}
                  formatter={(value, name) => [`${value} cases`, name]}
                />
                <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                  {chartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </Fade>

      {/* Toggle Button */}
      <Box sx={{
        display: 'flex',
        justifyContent: 'center',
        mb: 4
      }}>
        <Button
          variant="contained"
          onClick={() => setShowAll(!showAll)}
          endIcon={showAll ? <ExpandLessIcon /> : <ExpandMoreIcon />}
          sx={{
            background: 'linear-gradient(145deg, #3f51b5, #1e2a78 100%)',
            borderRadius: '12px',
            padding: '12px 24px',
            textTransform: 'none',
            fontSize: '1rem',
            fontWeight: 600,
            boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
            '&:hover': {
              background: 'linear-gradient(135deg, #334155 0%, #1e293b 100%)',
              boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1)'
            }
          }}
        >
          {showAll ? 'Show Less' : 'View All Root Causes'}
        </Button>
      </Box>

      {/* Table View */}
      <Collapse in={showAll}>
        <Fade in={showAll} timeout={500}>
          <TableContainer component={Paper} sx={{
            borderRadius: '16px',
            boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1)',
            overflow: 'hidden',
            mb: 4
          }}>
            <Table>
              <TableHead>
                <TableRow sx={{
                  background: 'linear-gradient(145deg, #3f51b5, #1e2a78)'
                }}>
                  <TableCell sx={{
                    fontWeight: 600,
                    color: '#ffffff',
                    fontSize: '0.875rem',
                    py: 2.5
                  }}>Root Cause</TableCell>
                  <TableCell align="right" sx={{
                    fontWeight: 600,
                    color: '#ffffff',
                    fontSize: '0.875rem',
                    py: 2.5
                  }}>Total Cases</TableCell>
                  <TableCell align="right" sx={{
                    fontWeight: 600,
                    color: '#ffffff',
                    fontSize: '0.875rem',
                    py: 2.5
                  }}>ElevAIte Usage Rate</TableCell>
                  <TableCell align="right" sx={{
                    fontWeight: 600,
                    color: '#ffffff',
                    fontSize: '0.875rem',
                    py: 2.5
                  }}>AHT (min)</TableCell>
                  <TableCell sx={{
                    fontWeight: 600,
                    color: '#ffffff',
                    fontSize: '0.875rem',
                    py: 2.5
                  }}>Top Symptoms</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {remainingIssues.map((issue) => (
                  <TableRow
                    key={issue.category}
                    sx={{
                      '&:hover': {
                        backgroundColor: '#f8fafc'
                      },
                      transition: 'background-color 0.2s'
                    }}
                  >
                    <TableCell sx={{
                      color: '#334155',
                      fontWeight: 500,
                      py: 2.5
                    }}>{issue.category}</TableCell>
                    <TableCell align="right" sx={{
                      color: '#334155',
                      fontWeight: 500,
                      py: 2.5
                    }}>{issue.total}</TableCell>
                    <TableCell align="right" sx={{
                      color: '#334155',
                      py: 2.5
                    }}>{issue.ElevAIte}%</TableCell>
                    <TableCell align="right" sx={{
                      color: '#334155',
                      py: 2.5
                    }}>{issue.aht}</TableCell>
                    <TableCell sx={{
                      color: '#64748b',
                      py: 2.5
                    }}>
                      {issue.subCategories.map(sub =>
                        `${sub.name} (${sub.count})`
                      ).join(', ')}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Fade>
      </Collapse>
    </Box>
  );
}

export default RootCause;