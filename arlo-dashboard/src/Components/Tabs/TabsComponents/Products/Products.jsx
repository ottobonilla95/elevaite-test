import React, { useEffect, useMemo, useState } from 'react';
import { Box, Grid, MenuItem, Select, FormControl, InputLabel, Typography, Card, CardHeader, CardContent, TableContainer, Table, TableHead, Paper, TableRow, TableCell, TableBody } from '@mui/material';
import { AccessAlarm, BugReport } from '@mui/icons-material';
import { TablePagination } from '@mui/material';
import { Bar, BarChart, ResponsiveContainer, XAxis, YAxis, Tooltip } from 'recharts';
import axios from 'axios';
function Products({ dateRange }) {
    const [excelData, setExcelData] = useState([]);
    const [productHierarchy, setProductHierarchy] = useState({
        products: new Set(),
        subProducts: new Map(),
    });
    const [selectedProduct, setSelectedProduct] = useState('all');
    const [selectedSubProduct, setSelectedSubProduct] = useState('all');
    const [page, setPage] = useState(0);
    const [rowsPerPage, setRowsPerPage] = useState(10);
    const [error, setError] = useState(null);
    const [loading, setLoading] = useState(true);

    //  useEffect in your Products component :
    useEffect(() => {
        const fetchData = async () => {
            if (!dateRange) {
                return; // Don't make the API call if dateRange is not available
            }
            try {
                setLoading(true);
                setError(null);
                console.log('Fetching data from API...'); // Debug log

                const response = await axios.get(`http://localhost:5000/api/products`, {
                    params: {
                        from: dateRange.fromDate,
                        to: dateRange.toDate
                    }
                });

                const data = response.data;

                // Filter out rows that don't contain products
                const filteredData = data.filter(row => row.Products);

                // Build hierarchy for dropdowns
                const hierarchy = filteredData.reduce((acc, row) => {
                    if (row.Products) {
                        acc.products.add(row.Products);
                        if (row['Sub Product']) {
                            if (!acc.subProducts.has(row.Products)) {
                                acc.subProducts.set(row.Products, new Set());
                            }
                            acc.subProducts.get(row.Products).add(row['Sub Product']);
                        }
                    }
                    return acc;
                }, {
                    products: new Set(),
                    subProducts: new Map()
                });

                console.log('Built hierarchy:', {
                    products: Array.from(hierarchy.products),
                    subProducts: Array.from(hierarchy.subProducts.entries())
                }); // Debug log

                setProductHierarchy(hierarchy);
                setExcelData(filteredData);
                setLoading(false);
            } catch (error) {
                console.error('Error fetching or processing data:', error);
                setError(error.message);
                setLoading(false);
            }
        };

        fetchData();
    }, [dateRange]);

    const filteredData = useMemo(() => {
        return excelData.filter(row => {
            if (selectedProduct !== 'all' && row.Products !== selectedProduct) return false;
            if (selectedSubProduct !== 'all' && row['Sub Product'] !== selectedSubProduct) return false;
            return true;
        });
    }, [excelData, selectedProduct, selectedSubProduct]);

    const metrics = useMemo(() => {
        const productCounts = {};

        filteredData.forEach(row => {
            if (row.Products) {
                productCounts[row.Products] = (productCounts[row.Products] || 0) + 1;
            }
        });

        const topProduct = Object.entries(productCounts)
            .sort(([, a], [, b]) => b - a)[0];

        const distributionData = Object.entries(productCounts)
            .map(([name, value]) => ({ name, value }))
            .sort((a, b) => b.value - a.value)
            .slice(0, 5);

        return {
            total: filteredData.length,
            topProduct: topProduct ? { name: topProduct[0], count: topProduct[1] } : null,
            distributionData
        };
    }, [filteredData]);

    return (
        <div>
            {loading && (
                <Typography variant="h6" sx={{ p: 2 }}>Loading...</Typography>
            )}

            {error && (
                <Typography variant="h6" color="error" sx={{ p: 2 }}>
                    Error: {error}
                </Typography>
            )}

            <Box sx={{ padding: '20px' }}>
                {/* Dropdowns */}
                <Grid container spacing={3} justifyContent="flex-start" alignItems="center">
                    <Grid item xs={12} sm={6}>
                        <FormControl fullWidth>
                            <InputLabel>All Products</InputLabel>
                            <Select
                                value={selectedProduct}
                                onChange={(e) => {
                                    setSelectedProduct(e.target.value);
                                    setSelectedSubProduct('all');
                                }}
                                label="All Products"
                            >
                                <MenuItem value="all">All Products</MenuItem>
                                {Array.from(productHierarchy.products).map((product) => (
                                    <MenuItem key={product} value={product}>{product}</MenuItem>
                                ))}
                            </Select>
                        </FormControl>
                    </Grid>

                    {selectedProduct !== 'all' && (
                        <Grid item xs={12} sm={6}>
                            <FormControl fullWidth>
                                <InputLabel>All Sub-Products</InputLabel>
                                <Select
                                    value={selectedSubProduct}
                                    onChange={(e) => setSelectedSubProduct(e.target.value)}
                                    label="Sub-Product"
                                >
                                    <MenuItem value="all">All Sub-Products</MenuItem>
                                    {Array.from(productHierarchy.subProducts.get(selectedProduct) || []).map((sub) => (
                                        <MenuItem key={sub} value={sub}>{sub}</MenuItem>
                                    ))}
                                </Select>
                            </FormControl>
                        </Grid>
                    )}
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
                                avatar={<AccessAlarm sx={{ color: '#1976d2' }} />}
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
                                title="Top Product"
                                sx={{ backgroundColor: '#f5f5f5', borderBottom: '1px solid #ddd' }}
                                avatar={<BugReport sx={{ color: '#ff5722' }} />}
                            />
                            <CardContent sx={{ flexGrow: 1 }}>
                                {metrics.topProduct && (
                                    <>
                                        <Typography variant="h6" sx={{ fontWeight: 'bold', color: '#ff5722' }}>
                                            {metrics.topProduct.name}
                                        </Typography>
                                        <Typography variant="body2" color="textSecondary">
                                            {metrics.topProduct.count} cases
                                        </Typography>
                                    </>
                                )}
                            </CardContent>
                        </Card>
                    </Grid>
                </Grid>

                {/* Product Distribution Chart */}
                <Grid container spacing={3} sx={{ marginTop: '20px' }}>
                    <Grid item xs={12}>
                        <Card sx={{ backgroundColor: '#fff', boxShadow: 3 }}>
                            <CardHeader title="Product Distribution" />
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
                                    fontSize: '1.2rem',
                                    fontWeight: 'bold'
                                }}
                            />
                            <CardContent sx={{ padding: '24px' }}>
                                <TableContainer component={Paper} sx={{ boxShadow: 2, borderRadius: 2 }}>
                                    <Table sx={{ minWidth: 650 }} aria-label="product performance table">
                                        <TableHead>
                                            <TableRow sx={{ backgroundColor: '#e3f2fd' }}>
                                                <TableCell sx={{ fontWeight: 'bold', color: '#1e2a78' }}>Product</TableCell>
                                                <TableCell sx={{ fontWeight: 'bold', color: '#1e2a78' }}>Sub Product</TableCell>
                                                <TableCell sx={{ fontWeight: 'bold', color: '#1e2a78' }}>Problem</TableCell>
                                                <TableCell sx={{ fontWeight: 'bold', color: '#1e2a78' }}>Root Cause</TableCell>
                                                <TableCell sx={{ fontWeight: 'bold', color: '#1e2a78' }}>AHT</TableCell>

                                            </TableRow>
                                        </TableHead>
                                        <TableBody>
                                            {filteredData
                                                .slice(page * rowsPerPage, (page + 1) * rowsPerPage)
                                                .map((row, index) => (
                                                    <TableRow key={index} sx={{ '&:hover': { backgroundColor: '#f0f0f0' }, transition: 'background-color 0.3s' }}>
                                                        <TableCell>{row.Products || ''}</TableCell>
                                                        <TableCell>{row['Sub Product'] || ''}</TableCell>
                                                        <TableCell>{row.Problem || ''}</TableCell>
                                                        <TableCell>{row['Root cause'] || ''}</TableCell>
                                                        <TableCell>{row.AHT || ''}</TableCell>

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
        </div>
    );
}

export default Products;