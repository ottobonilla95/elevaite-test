import React, { useState, useEffect } from 'react';
import { CircularProgress as MUICircularProgress, Card, CardContent, Typography, Grid, CardHeader, Box, List, ListItem, ListItemText, Icon, Divider, Dialog, DialogTitle, DialogContent, DialogActions, Button, Table, TableBody, TableCell, TableHead, TableRow } from '@mui/material';
import ThumbUpIcon from '@mui/icons-material/ThumbUp';
import ThumbDownIcon from '@mui/icons-material/ThumbDown';
import { ResponsiveContainer, Tooltip, Legend, XAxis, YAxis, BarChart, Bar } from 'recharts';
import axios from 'axios';

function Summary({ dateRange }) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [data, setData] = useState({
    totalSessions: 0,
    aht: '00:00',
    resolutionRate: 0,
    upvotes: 0,
    downvotes: 0,
    rootCauses: [],
    feedback: {
      mostUpvoted: [],
      mostDownvoted: []
    }
  });

  // Dialog state
  const [dialogOpen, setDialogOpen] = useState(false);
  const [selectedFeedback, setSelectedFeedback] = useState(null);
  const [feedbackDetails, setFeedbackDetails] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      if (!dateRange) return;

      try {
        const [summaryResponse, feedbackResponse] = await Promise.all([
          axios.get(`http://localhost:5000/api/summary-data`, {
            params: {
              from: dateRange.fromDate,
              to: dateRange.toDate
            }
          }),
          axios.get(`http://localhost:5000/api/feedback`, {
            params: {
              from: dateRange.fromDate,
              to: dateRange.toDate
            }
          })
        ]);

        console.log('Summary Response:', summaryResponse.data);
        console.log('Feedback Response:', feedbackResponse.data);

        // Transform root causes data
        if (summaryResponse.data.rootCauses) {
          summaryResponse.data.rootCauses = summaryResponse.data.rootCauses.map(item => ({
            name: item.name || '',
            sessions: item.sessions || 0,
            percentage: item.percentage || 0
          }));
        }

        // Filter out the first item from both upvoted and downvoted arrays
        const filteredResponse = {
          ...feedbackResponse.data,
          mostUpvoted: feedbackResponse.data.mostUpvoted.slice(1, 4),
          mostDownvoted: feedbackResponse.data.mostDownvoted.slice(1, 4)
        };
        console.log('Filtered Feedback Response:', filteredResponse);

        setData({
          ...summaryResponse.data,
          feedback: filteredResponse
        });
      } catch (error) {
        console.error('Error fetching data:', error);
        setError(error.message);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [dateRange]);

  const handleFeedbackClick = async (feedbackItem, type) => {
    try {
      if (!feedbackItem.transcript_ids || feedbackItem.transcript_ids.length === 0) {
        console.error('No transcript IDs available');
        return;
      }

      const response = await axios.get(`http://localhost:5000/api/feedback-details`, {
        params: {
          item: feedbackItem.item,
          type,
          from: dateRange?.fromDate,
          to: dateRange?.toDate,
          transcript_ids: feedbackItem.transcript_ids.join(',')
        }
      });
      console.log('Feedback Details Response:', response.data);



      if (response.data && Array.isArray(response.data)) {
        setFeedbackDetails(response.data);
        setSelectedFeedback({
          ...feedbackItem,
          type
        });
        setDialogOpen(true);
      } else {
        console.error('Invalid response format:', response.data);
      }
    } catch (error) {
      console.error('Error fetching feedback details:', error);
    }
  };

  const FeedbackDialog = () => (
    <Dialog
      open={dialogOpen}
      onClose={() => setDialogOpen(false)}
      maxWidth="md"
      fullWidth
    >
      <DialogTitle>
        <Typography variant="h6">
          {selectedFeedback?.item}
        </Typography>
        <Typography variant="subtitle2" color="textSecondary">
          {selectedFeedback?.category} - {selectedFeedback?.type === 'upvote' ? 'Upvoted' : 'Downvoted'}
        </Typography>
      </DialogTitle>
      <DialogContent>
        {feedbackDetails && feedbackDetails.length > 0 ? (
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Transcript ID</TableCell>
                <TableCell>Product</TableCell>
                <TableCell>Problem</TableCell>
                <TableCell>Root Cause</TableCell>
                <TableCell>Symptoms</TableCell>
                <TableCell align="center">Status</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {feedbackDetails.map((detail, index) => (
                <TableRow key={index}>
                  <TableCell>{detail.chat_transcript_id}</TableCell>
                  <TableCell>{detail.product || 'N/A'}</TableCell>
                  <TableCell>{detail.problem}</TableCell>
                  <TableCell>{detail.root_cause}</TableCell>
                  <TableCell>{detail.symptoms}</TableCell>
                  <TableCell align="center">
                    <Box display="flex" alignItems="center" justifyContent="center" gap={1}>
                      {detail.upvotes > 0 ? (
                        <ThumbUpIcon color="success" fontSize="small" />
                      ) : (
                        <ThumbDownIcon color="error" fontSize="small" />
                      )}
                    </Box>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        ) : (
          <Typography variant="body1" align="center" sx={{ py: 3 }}>
            No detailed information available for this feedback.
          </Typography>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={() => setDialogOpen(false)}>Close</Button>
      </DialogActions>
    </Dialog>
  );

  const calculateSatisfaction = (upvotes, downvotes) => {
    console.log('Calculating Satisfaction:', { upvotes, downvotes });
    const satisfaction = upvotes + downvotes === 0 ? 0 : (upvotes / (upvotes + downvotes) * 100);
    console.log('Calculated Satisfaction:', satisfaction);
    return satisfaction;
  };
  if (loading) return (
    <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
      <MUICircularProgress />
    </Box>
  );

  if (error) return (
    <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
      <Typography color="error">Error: {error}</Typography>
    </Box>
  );

  return (
    <div>
      <Box sx={{ padding: '20px' }}>
        {/* Metric Cards */}
        <Grid container spacing={3}>
          {/* Total Sessions Card */}
          <Grid item xs={12} sm={6} md={4}>
            <Card sx={{
              backgroundColor: '#fff',
              boxShadow: 5,
              borderRadius: 2,
              transition: 'all 0.3s ease',
              padding: '16px',
              '&:hover': {
                transform: 'scale(1.05)',
                boxShadow: 8
              }
            }}>
              <CardHeader
                title="Total Sessions"
                sx={{
                  textAlign: 'center',
                  background: 'linear-gradient(145deg, #3f51b5, #1e2a78)',
                  color: '#fff',
                  padding: '12px 16px',
                  borderRadius: '8px',
                  fontSize: '1.2rem',
                  fontWeight: 'bold'
                }}
              />
              <CardContent sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '16px' }}>
                <Box sx={{ position: 'relative', display: 'inline-flex' }}>
                  <MUICircularProgress
                    variant="determinate"
                    value={(data.totalSessions / 10000) * 100}
                    size={90}
                    thickness={6}
                    sx={{
                      color: '#4caf50',
                      '& .MuiCircularProgress-circle': {
                        strokeLinecap: 'round'
                      }
                    }}
                  />
                  <Box
                    position="absolute"
                    top="50%"
                    left="50%"
                    sx={{ transform: 'translate(-50%, -50%)' }}
                  >
                    <Typography variant="h6" color="textSecondary" fontWeight="bold">
                      {data.totalSessions}
                    </Typography>
                  </Box>
                </Box>
                <Typography variant="body2" color="textSecondary" align="center" sx={{ marginTop: '12px' }}>
                  Support Interactions
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          {/* Average Handle Time Card */}
          <Grid item xs={12} sm={6} md={4}>
            <Card sx={{
              backgroundColor: '#fff',
              boxShadow: 5,
              borderRadius: 2,
              '&:hover': {
                transform: 'scale(1.05)',
                boxShadow: 8
              },
              transition: 'all 0.3s ease',
              padding: '16px'
            }}>
              <CardHeader
                title="Average Handle Time"
                sx={{
                  textAlign: 'center',
                  background: 'linear-gradient(145deg, #3f51b5, #1e2a78)',
                  color: '#fff',
                  padding: '12px 16px',
                  borderRadius: '8px',
                  fontSize: '1.2rem',
                  fontWeight: 'bold'
                }}
              />
              <CardContent sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '16px' }}>
                <Box sx={{ position: 'relative', display: 'inline-flex' }}>
                  <MUICircularProgress
                    variant="determinate"
                    value={((parseInt(data.aht.split(':')[0], 10) * 60 + parseInt(data.aht.split(':')[1], 10)) / (30 * 60)) * 100}
                    size={90}
                    thickness={6}
                    sx={{
                      color: '#4caf50',
                      '& .MuiCircularProgress-circle': {
                        strokeLinecap: 'round'
                      }
                    }}
                  />
                  <Box
                    position="absolute"
                    top="50%"
                    left="50%"
                    sx={{ transform: 'translate(-50%, -50%)' }}
                  >
                    <Typography variant="h6" color="textSecondary" fontWeight="bold">
                      {data.aht}
                    </Typography>
                  </Box>
                </Box>
                <Typography variant="body2" color="textSecondary" align="center" sx={{ marginTop: '12px' }}>
                  Minutes per session
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          {/* ElevAIte Usage Card */}
          <Grid item xs={12} sm={6} md={4}>
            <Card sx={{
              backgroundColor: '#fff',
              boxShadow: 5,
              borderRadius: 2,
              '&:hover': {
                transform: 'scale(1.05)',
                boxShadow: 8
              },
              transition: 'all 0.3s ease',
              padding: '16px'
            }}>
              <CardHeader
                title="ElevAIte Usage"
                sx={{
                  textAlign: 'center',
                  background: 'linear-gradient(145deg, #3f51b5, #1e2a78)',
                  color: '#fff',
                  padding: '12px 16px',
                  borderRadius: '8px',
                  fontSize: '1.2rem',
                  fontWeight: 'bold'
                }}
              />
              <CardContent sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '16px' }}>
                <Box sx={{ position: 'relative', display: 'inline-flex' }}>
                  <MUICircularProgress
                    variant="determinate"
                    value={calculateSatisfaction(data.upvotes, data.downvotes)}
                    size={90}
                    thickness={6}
                    sx={{
                      color: calculateSatisfaction(data.upvotes, data.downvotes) > 10 ? '#4caf50' : '#4caf50',
                      '& .MuiCircularProgress-circle': {
                        strokeLinecap: 'round'
                      }
                    }}
                  />
                  <Box
                    position="absolute"
                    top="50%"
                    left="50%"
                    sx={{ transform: 'translate(-50%, -50%)' }}
                  >
                    <Typography variant="h6" color="textSecondary" fontWeight="bold">
                      {calculateSatisfaction(data.upvotes, data.downvotes).toFixed(1)}%
                    </Typography>
                  </Box>
                </Box>
                <Typography variant="body2" color="textSecondary" align="center" sx={{ marginTop: '12px' }}>
                  Based on {data.upvotes + data.downvotes} ratings
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Feedback Section */}
        <Grid container spacing={3} sx={{ marginTop: '20px' }}>
          {/* Most Upvoted Feedback */}
          <Grid item xs={12} sm={6}>
            <Card sx={{ backgroundColor: '#e8f5e9', height: '100%' }}>
              <CardHeader title="Most Upvoted Feedback" />
              <CardContent>
                <List>
                  {data.feedback.mostUpvoted.map((feedbackItem, index) => (
                    <Box key={index} sx={{ marginBottom: index < data.feedback.mostUpvoted.length - 1 ? '10px' : '0' }}>
                      <ListItem
                        button
                        onClick={() => handleFeedbackClick(feedbackItem, 'upvote')}
                        sx={{ '&:hover': { backgroundColor: 'rgba(0, 0, 0, 0.04)' } }}
                      >
                        <Icon sx={{ color: 'green', marginRight: '10px' }}><ThumbUpIcon /></Icon>
                        <ListItemText
                          primary={
                            <Typography variant="subtitle1">
                              {feedbackItem.item} ({feedbackItem.count})
                            </Typography>
                          }
                          secondary={
                            <Typography variant="body2" sx={{ color: 'text.secondary' }}>
                              {feedbackItem.category}
                            </Typography>
                          }
                        />
                      </ListItem>
                      {index < data.feedback.mostUpvoted.length - 1 && <Divider />}
                    </Box>
                  ))}
                </List>
              </CardContent>
            </Card>
          </Grid>

          {/* Most Downvoted Feedback */}
          <Grid item xs={12} sm={6}>
            <Card sx={{ backgroundColor: '#ffebee', height: '100%' }}>
              <CardHeader title="Most Downvoted Feedback" />
              <CardContent>
                <List>
                  {data.feedback.mostDownvoted.map((feedbackItem, index) => (
                    <Box key={index} sx={{ marginBottom: index < data.feedback.mostDownvoted.length - 1 ? '10px' : '0' }}>
                      <ListItem
                        button
                        onClick={() => handleFeedbackClick(feedbackItem, 'downvote')}
                        sx={{ '&:hover': { backgroundColor: 'rgba(0, 0, 0, 0.04)' } }}
                      >
                        <Icon sx={{ color: 'red', marginRight: '10px' }}><ThumbDownIcon /></Icon>
                        <ListItemText
                          primary={
                            <Typography variant="subtitle1">
                              {feedbackItem.item} ({feedbackItem.count})
                            </Typography>
                          }
                          secondary={
                            <Typography variant="body2" sx={{ color: 'text.secondary' }}>
                              {feedbackItem.category}
                            </Typography>
                          }
                        />
                      </ListItem>
                      {index < data.feedback.mostDownvoted.length - 1 && <Divider />}
                    </Box>
                  ))}
                </List>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Root Causes Chart */}
        <Grid container sx={{ marginTop: '20px' }}>
          <Grid item xs={12}>
            <Card sx={{ backgroundColor: '#fff', boxShadow: 6, borderRadius: '12px', overflow: 'hidden' }}>
              <CardHeader
                title="Top Issues Distribution"
                sx={{
                  textAlign: 'center',
                  background: 'linear-gradient(145deg, #3f51b5, #1e2a78)',
                  color: '#fff',
                  padding: '16px',
                  fontSize: '1.5rem',
                  fontWeight: 'bold'
                }}
              />
              <CardContent sx={{ padding: '24px' }}>
                <ResponsiveContainer width="100%" height={350}>
                  <BarChart
                    data={data.rootCauses.slice(1)}
                    margin={{ top: 20, right: 30, left: 0, bottom: 20 }}
                  >
                    <XAxis
                      dataKey="name"
                      tick={{ fill: '#666', fontSize: '0.85rem' }}
                      axisLine={{ stroke: '#ccc' }}
                      tickLine={{ stroke: '#ccc' }}
                    />
                    <YAxis
                      tick={{ fill: '#666', fontSize: '0.85rem' }}
                      axisLine={{ stroke: '#ccc' }}
                      tickLine={{ stroke: '#ccc' }}
                    />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#ffffff',
                        border: '1px solid #ddd',
                        borderRadius: '8px',
                        fontSize: '0.9rem'
                      }}
                      cursor={{ fill: 'rgba(0, 0, 0, 0.1)' }}
                    />
                    <Legend
                      wrapperStyle={{
                        paddingTop: '10px',
                        textAlign: 'center',
                        fontSize: '0.9rem'
                      }}
                    />
                    <Bar
                      dataKey="sessions"
                      fill="url(#gradient)"
                      barSize={30}
                      radius={[4, 4, 0, 0]}
                    />
                    <defs>
                      <linearGradient id="gradient" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="#42a5f5" />
                        <stop offset="100%" stopColor="#1e88e5" />
                      </linearGradient>
                    </defs>
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Box>

      {/* Feedback Details Dialog */}
      <FeedbackDialog />
    </div>
  );
}

export default Summary;