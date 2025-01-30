import React, { useEffect, useMemo, useState } from 'react';
import { Box, Card, CardContent, CardHeader, FormControl, Grid, InputLabel, MenuItem, Paper, Select, Table, TableBody, TableCell, TableContainer, TableHead, TablePagination, TableRow, Typography } from '@mui/material';
import { BugReport, Insights, Task } from '@mui/icons-material';
import { Bar, BarChart, ResponsiveContainer, XAxis, YAxis, Tooltip } from 'recharts';
import _ from 'lodash';
import axios from 'axios';

function Problems({ dateRange }) {
    const [data, setData] = useState([]);
    const [problems, setProblems] = useState([]);
    const [selectedProblem, setSelectedProblem] = useState("all_problems");
    const [rootCauses, setRootCauses] = useState([]);
    const [filteredData, setFilteredData] = useState([]);
    const [selectedRootCause, setSelectedRootCause] = useState("all_causes");
    const [symptoms, setSymptoms] = useState([]);
    const [selectedSymptom, setSelectedSymptom] = useState("all_symptoms");
    const [page, setPage] = useState(0);
    const [rowsPerPage, setRowsPerPage] = useState(10);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [staticData, setStaticData] = useState([]);
    useEffect(() => {
        const fetchData = async () => {
            if (!dateRange) {
                return; // Don't make the API call if dateRange is not available
            }

            try {
                const response = await axios.get(`http://localhost:5000/api/problems-data`, {
                    params: {
                        from: dateRange.fromDate,
                        to: dateRange.toDate
                    }
                });
                const responseData = response.data;
                console.log("responsedata", responseData)


                if (responseData && responseData.length > 0) {
                    // Filter out "disconnected phone" from the initial data
                    const filteredResponseData = responseData.filter(row => row.Problem !== "disconnected phone");

                    const uniqueProblems = _.uniq(filteredResponseData.map(row => row.Problem))
                        .filter(problem => problem !== "" && problem !== 0)
                        .sort();
                    const uniqueSymptoms = _.uniq(filteredResponseData.map(row => row.Symptoms))
                        .filter(symptom => symptom !== "" && symptom !== 0)
                        .sort();

                    setProblems(uniqueProblems);
                    setSymptoms(uniqueSymptoms);
                    setData(filteredResponseData);      // Use filtered data here
                    setFilteredData(filteredResponseData);
                    setStaticData(filteredResponseData); // And here
                }
                setLoading(false);
            } catch (error) {
                console.error('Error fetching data:', error);
                setError(error.message);
                setLoading(false);
            }
        };
        fetchData();
    }, [dateRange]);
    useEffect(() => {
        let filteredResults = data;

        if (selectedProblem !== "all_problems") {
            filteredResults = filteredResults.filter(row => row.Problem === selectedProblem);
        }

        if (selectedRootCause !== "all_causes") {
            filteredResults = filteredResults.filter(row => row['Root cause'] === selectedRootCause);
        }

        if (selectedSymptom !== "all_symptoms") {
            filteredResults = filteredResults.filter(row => row.Symptoms === selectedSymptom);
        }




        setFilteredData(filteredResults);

        if (selectedProblem !== "all_problems") {
            const uniqueRootCauses = _.uniq(filteredResults.map(row => row['Root cause']))
                .filter(cause => cause !== "" && cause !== null)
                .sort();
            setRootCauses(uniqueRootCauses);
        } else {
            setRootCauses([]);
        }

        if (selectedProblem !== "all_problems" || selectedRootCause !== "all_causes") {
            const uniqueSymptoms = _.uniq(filteredResults.map(row => row.Symptoms))
                .filter(symptom => symptom !== "" && symptom !== null)
                .sort();
            setSymptoms(uniqueSymptoms);
        } else {
            setSymptoms([]);
        }
    }, [selectedProblem, selectedRootCause, selectedSymptom, data]);
    const metrics = useMemo(() => {
        // Static metrics
        const staticProblemCounts = {};
        staticData.forEach(row => {
            if (row.Problem) {
                staticProblemCounts[row.Problem] = (staticProblemCounts[row.Problem] || 0) + 1;
            }
        });

        const topProblem = Object.entries(staticProblemCounts)
            .sort(([, a], [, b]) => b - a)[1];

        const distributionData = Object.entries(staticProblemCounts)
            .map(([name, value]) => ({ name, value }))
            .sort((a, b) => b.value - a.value)
            .slice(1, 7);

        // Filtered metrics
        const total = filteredData.length;
        const aiUsed = filteredData.filter(row => row['AI Usage ID'] === 'Yes').length;

        return {
            total,
            aiUsed,
            aiPercentage: total ? ((aiUsed / total) * 100).toFixed(1) : 0,
            topProblem: topProblem ? { name: topProblem[0], count: topProblem[1] } : null,
            distributionData
        };
    }, [staticData, filteredData]);

    if (loading) return <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>Loading...</Box>;
    if (error) return <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>Error: {error}</Box>;

    return (
        <Box sx={{ padding: '20px' }}>
            {/* Filters */}
            <Grid container spacing={2} justifyContent="flex-start" alignItems="center">
                <Grid item xs={12} sm={4}>
                    <FormControl fullWidth>
                        <InputLabel>All Issues</InputLabel>
                        <Select
                            value={selectedProblem}
                            onChange={(e) => setSelectedProblem(e.target.value)}
                            label="All Issues"
                        >
                            <MenuItem value="all_problems">All Issues</MenuItem>
                            {problems.map((problem) => (
                                <MenuItem key={problem} value={problem}>{problem}</MenuItem>
                            ))}
                        </Select>
                    </FormControl>
                </Grid>

                <Grid item xs={12} sm={4}>
                    <FormControl fullWidth>
                        <InputLabel>All Root Causes</InputLabel>
                        <Select
                            value={selectedRootCause}
                            onChange={(e) => setSelectedRootCause(e.target.value)}
                            label="All Root Causes"
                            disabled={!selectedProblem || selectedProblem === "all_problems"}
                        >
                            <MenuItem value="all_causes">All Root Causes</MenuItem>
                            {rootCauses.map((cause) => (
                                <MenuItem key={cause} value={cause}>{cause}</MenuItem>
                            ))}
                        </Select>
                    </FormControl>
                </Grid>

                <Grid item xs={12} sm={4}>
                    <FormControl fullWidth>
                        <InputLabel>All Symptoms</InputLabel>
                        <Select
                            value={selectedSymptom}
                            onChange={(e) => setSelectedSymptom(e.target.value)}
                            label="All Symptoms"
                            disabled={!selectedProblem || selectedProblem === "all_problems"}
                        >
                            <MenuItem value="all_symptoms">All Symptoms</MenuItem>
                            {symptoms.map((symptom) => (
                                <MenuItem key={symptom} value={symptom}>{symptom}</MenuItem>
                            ))}
                        </Select>
                    </FormControl>
                </Grid>
            </Grid>

            {/* Metric Cards */}
            <Grid container spacing={3} sx={{ marginTop: '20px' }}>
                <Grid item xs={12} sm={6} md={3}>
                    <Card sx={{
                        backgroundColor: '#fff',
                        boxShadow: 3,
                        borderRadius: 2,
                        '&:hover': { boxShadow: 6 },
                        transition: 'all 0.3s',
                        display: 'flex',
                        flexDirection: 'column',
                        height: '100%'
                    }}>
                        <CardHeader
                            title="Total Cases"
                            sx={{ backgroundColor: '#f5f5f5', borderBottom: '1px solid #ddd' }}
                            avatar={<Task sx={{ color: '#1976d2' }} />}
                        />
                        <CardContent sx={{ flexGrow: 1 }}>
                            <Typography variant="h3" sx={{ fontWeight: 'bold', color: '#1976d2' }}>
                                {metrics.total}
                            </Typography>
                            <Typography variant="body2" color="textSecondary">
                                Total cases
                            </Typography>
                        </CardContent>
                    </Card>
                </Grid>

                <Grid item xs={12} sm={6} md={3}>
                    <Card sx={{
                        backgroundColor: '#fff',
                        boxShadow: 3,
                        borderRadius: 2,
                        '&:hover': { boxShadow: 6 },
                        transition: 'all 0.3s',
                        display: 'flex',
                        flexDirection: 'column',
                        height: '100%'
                    }}>
                        <CardHeader
                            title="ElevAIte Assisted Cases"
                            sx={{ backgroundColor: '#f5f5f5', borderBottom: '1px solid #ddd' }}
                            avatar={<Insights sx={{ color: '#ff5722' }} />}
                        />
                        <CardContent sx={{ flexGrow: 1 }}>
                            <Typography variant="h6" sx={{ fontWeight: 'bold', color: '#ff5722' }}>
                                {metrics.aiUsed} ({metrics.aiPercentage}%)
                            </Typography>
                            <Typography variant="body2" color="textSecondary">
                                AI-assisted cases
                            </Typography>
                        </CardContent>
                    </Card>
                </Grid>

                <Grid item xs={12} sm={6} md={3}>
                    <Card sx={{
                        backgroundColor: '#fff',
                        boxShadow: 3,
                        borderRadius: 2,
                        '&:hover': { boxShadow: 6 },
                        transition: 'all 0.3s',
                        display: 'flex',
                        flexDirection: 'column',
                        height: '100%'
                    }}>
                        <CardHeader
                            title="Top Problem"
                            sx={{ backgroundColor: '#f5f5f5', borderBottom: '1px solid #ddd' }}
                            avatar={<BugReport sx={{ color: '#1976d2' }} />}
                        />
                        <CardContent sx={{ flexGrow: 1 }}>
                            {metrics.topProblem && (
                                <>
                                    <Typography variant="h6" sx={{ fontWeight: 'bold', color: '#1976d2' }}>
                                        {metrics.topProblem.name}
                                    </Typography>
                                    <Typography variant="body2" color="textSecondary">
                                        {metrics.topProblem.count} cases
                                    </Typography>
                                </>
                            )}
                        </CardContent>
                    </Card>
                </Grid>
            </Grid>

            {/* Problem Distribution Chart */}
            <Grid container spacing={3} sx={{ marginTop: '20px' }}>
                <Grid item xs={12}>
                    <Card sx={{ backgroundColor: '#fff', boxShadow: 3 }}>
                        <CardHeader title="Problem Distribution" />
                        <CardContent>
                            <ResponsiveContainer width="100%" height={400}>
                                <BarChart data={metrics.distributionData}>
                                    <XAxis dataKey="name" />
                                    <YAxis />
                                    <Tooltip />
                                    <Bar dataKey="value" fill="#8884d8" />
                                </BarChart>
                            </ResponsiveContainer>
                        </CardContent>
                    </Card>
                </Grid>
            </Grid>

            {/* Data Table */}
            <Grid container spacing={3} sx={{ marginTop: '20px' }}>
                <Grid item xs={12}>
                    <Card sx={{ backgroundColor: '#fff', boxShadow: 3, borderRadius: 2, '&:hover': { boxShadow: 6 }, transition: 'all 0.3s ease' }}>
                        <CardHeader
                            title="Case Details"
                            sx={{
                                background: 'linear-gradient(145deg, #3f51b5, #1e2a78)',
                                color: '#fff',
                                textAlign: 'center',
                                padding: '16px',
                                '& .MuiCardHeader-title': {
                                    fontSize: '1.2rem',
                                    fontWeight: 'bold'
                                }
                            }}
                        />
                        <CardContent sx={{ padding: '24px' }}>
                            <TableContainer component={Paper} sx={{ boxShadow: 2, borderRadius: 2 }}>
                                <Table sx={{ minWidth: 650 }} aria-label="problem details table">
                                    <TableHead>
                                        <TableRow sx={{ backgroundColor: '#e3f2fd' }}>
                                            <TableCell sx={{ fontWeight: 'bold', color: '#1e2a78' }}>Issues</TableCell>
                                            <TableCell sx={{ fontWeight: 'bold', color: '#1e2a78' }}>Root Cause</TableCell>
                                            <TableCell sx={{ fontWeight: 'bold', color: '#1e2a78' }}>Symptoms</TableCell>
                                            <TableCell sx={{ fontWeight: 'bold', color: '#1e2a78' }}>Elevaite AI Usage</TableCell>
                                            <TableCell sx={{ fontWeight: 'bold', color: '#1e2a78' }}>AHT</TableCell>
                                        </TableRow>
                                    </TableHead>
                                    <TableBody>
                                        {filteredData
                                            .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
                                            .map((row, index) => (
                                                <TableRow key={`${row.Problem}-${index}`} sx={{ '&:hover': { backgroundColor: '#f0f0f0' }, transition: 'background-color 0.3s' }}>
                                                    <TableCell>{row.Problem}</TableCell>
                                                    <TableCell>{row['Root cause']}</TableCell>
                                                    <TableCell>{row.Symptoms}</TableCell>
                                                    <TableCell>{row['AI Usage ID']}</TableCell>
                                                    <TableCell>
                                                        {row['Chat Duration'] !== 'N/A' ? (
                                                            <Box>
                                                                <Box sx={{ fontWeight: 'bold' }}>{row['Chat Duration']}</Box>
                                                                <Box sx={{ color: 'text.secondary', fontSize: '0.75rem' }}>minutes</Box>
                                                            </Box>
                                                        ) : (
                                                            <Box sx={{ fontWeight: 'bold' }}>N/A</Box>
                                                        )}
                                                    </TableCell>
                                                </TableRow>
                                            ))}
                                    </TableBody>
                                </Table>
                                <TablePagination
                                    rowsPerPageOptions={[10, 20, 30]}
                                    component="div"
                                    count={filteredData.length}
                                    rowsPerPage={rowsPerPage}
                                    page={page}
                                    onPageChange={(event, newPage) => setPage(newPage)}
                                    onRowsPerPageChange={(event) => {
                                        setRowsPerPage(parseInt(event.target.value, 10));
                                        setPage(0);
                                    }}
                                />
                            </TableContainer>
                        </CardContent>
                    </Card>
                </Grid>
            </Grid>
        </Box>
    );
}

export default Problems;