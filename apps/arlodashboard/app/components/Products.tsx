import React, { useEffect, useMemo, useState } from 'react';
import axios from 'axios';
import { Bar, BarChart, ResponsiveContainer, XAxis, YAxis, Tooltip } from 'recharts';

// Define TypeScript interfaces
interface DateRange {
    fromDate: string;
    toDate: string;
}

interface ProductsProps {
    dateRange: DateRange | null;
}

interface ProductData {
    Products: string;
    'Sub Product': string;
    Problem: string;
    'Root cause': string;
    AHT: string;
}

interface ProductHierarchy {
    products: Set<string>;
    subProducts: Map<string, Set<string>>;
}

interface Metrics {
    total: number;
    topProduct: { name: string; count: number } | null;
    distributionData: { name: string; value: number }[];
}

// Custom tooltip component for the chart
const CustomTooltip: React.FC<any> = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
        return (
            <div className="bg-white p-3 border border-gray-200 rounded shadow-md">
                <p className="font-medium">{label}</p>
                <p className="text-blue-600">{`Cases: ${payload[0].value}`}</p>
            </div>
        );
    }
    return null;
};

const Products: React.FC<ProductsProps> = ({ dateRange }) => {
    const [excelData, setExcelData] = useState<ProductData[]>([]);
    const [productHierarchy, setProductHierarchy] = useState<ProductHierarchy>({
        products: new Set<string>(),
        subProducts: new Map<string, Set<string>>(),
    });
    const [selectedProduct, setSelectedProduct] = useState<string>('all');
    const [selectedSubProduct, setSelectedSubProduct] = useState<string>('all');
    const [page, setPage] = useState<number>(0);
    const [rowsPerPage, setRowsPerPage] = useState<number>(10);
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState<boolean>(true);

    // Items to filter out
    const excludedItems = ["Offline", "Disconnected Phone"];

    useEffect(() => {
        const fetchData = async () => {
            if (!dateRange) {
                return; // Don't make the API call if dateRange is not available
            }
            try {
                setLoading(true);
                setError(null);
                console.log('Fetching products data from API...'); // Debug log

                const response = await axios.get(`http://localhost:5000/api/products`, {
                    params: {
                        from: dateRange.fromDate,
                        to: dateRange.toDate
                    }
                });

                const data = response.data as ProductData[];

                // Filter out rows that don't contain products and exclude specific items
                const filteredData = data.filter(row =>
                    row.Products &&
                    !excludedItems.includes(row.Products) &&
                    !excludedItems.includes(row['Root cause'])
                );

                // Build hierarchy for dropdowns
                const hierarchy = filteredData.reduce((acc: ProductHierarchy, row) => {
                    if (row.Products) {
                        acc.products.add(row.Products);
                        if (row['Sub Product']) {
                            if (!acc.subProducts.has(row.Products)) {
                                acc.subProducts.set(row.Products, new Set<string>());
                            }
                            acc.subProducts.get(row.Products)?.add(row['Sub Product']);
                        }
                    }
                    return acc;
                }, {
                    products: new Set<string>(),
                    subProducts: new Map<string, Set<string>>()
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
                setError(error instanceof Error ? error.message : 'An unknown error occurred');
                setLoading(false);
            }
        };

        fetchData();
    }, [dateRange]);

    const filteredData = useMemo(() => {
        return excelData.filter(row => {
            // Apply product and sub-product filters
            if (selectedProduct !== 'all' && row.Products !== selectedProduct) return false;
            if (selectedSubProduct !== 'all' && row['Sub Product'] !== selectedSubProduct) return false;

            // Make sure the excluded items don't appear
            if (excludedItems.includes(row.Products) || excludedItems.includes(row['Root cause'])) return false;

            return true;
        });
    }, [excelData, selectedProduct, selectedSubProduct]);

    const metrics: Metrics = useMemo(() => {
        const productCounts: Record<string, number> = {};

        filteredData.forEach(row => {
            if (row.Products) {
                productCounts[row.Products] = (productCounts[row.Products] || 0) + 1;
            }
        });

        const topProductArray = Object.entries(productCounts)
            .sort(([, a], [, b]) => b - a);

        const topProduct = topProductArray.length > 0 ?
            { name: topProductArray[0][0], count: topProductArray[0][1] } : null;

        const distributionData = Object.entries(productCounts)
            .map(([name, value]) => ({ name, value }))
            .sort((a, b) => b.value - a.value)
            .slice(0, 5);

        return {
            total: filteredData.length,
            topProduct,
            distributionData
        };
    }, [filteredData]);

    const handleChangePage = (event: unknown, newPage: number) => {
        setPage(newPage);
    };

    const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLSelectElement>) => {
        setRowsPerPage(parseInt(event.target.value, 10));
        setPage(0);
    };

    return (
        <div className="overflow-y-auto">
            {loading && (
                <div className="flex justify-center items-center p-4">
                    <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-blue-500"></div>
                </div>
            )}

            {error && (
                <div className="p-4 text-red-600 font-medium">
                    Error: {error}
                </div>
            )}

            <div className="p-5">
                {/* Dropdowns */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">All Products</label>
                        <select
                            className="w-full border border-gray-300 rounded-md p-2 focus:ring-blue-500 focus:border-blue-500"
                            value={selectedProduct}
                            onChange={(e) => {
                                setSelectedProduct(e.target.value);
                                setSelectedSubProduct('all');
                            }}
                        >
                            <option value="all">All Products</option>
                            {Array.from(productHierarchy.products).map((product) => (
                                <option key={product} value={product}>{product}</option>
                            ))}
                        </select>
                    </div>

                    {selectedProduct !== 'all' && (
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">All Sub-Products</label>
                            <select
                                className="w-full border border-gray-300 rounded-md p-2 focus:ring-blue-500 focus:border-blue-500"
                                value={selectedSubProduct}
                                onChange={(e) => setSelectedSubProduct(e.target.value)}
                            >
                                <option value="all">All Sub-Products</option>
                                {Array.from(productHierarchy.subProducts.get(selectedProduct) || []).map((sub) => (
                                    <option key={sub} value={sub}>{sub}</option>
                                ))}
                            </select>
                        </div>
                    )}
                </div>

                {/* Metric Cards */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                    {/* Total Cases Card */}
                    <div className="bg-white rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-105">
                        <div className="bg-gradient-to-r from-blue-700 to-indigo-900 text-white text-center py-3 px-4 rounded-t-lg text-lg font-bold">
                            Total Cases
                        </div>
                        <div className="flex flex-col items-center p-4">
                            <div className="text-4xl font-bold text-blue-600 my-2">
                                {metrics.total}
                            </div>
                            <p className="text-sm text-gray-500">
                                Total cases
                            </p>
                        </div>
                    </div>

                    {/* Top Product Card */}
                    <div className="bg-white rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-105">
                        <div className="bg-gradient-to-r from-blue-700 to-indigo-900 text-white text-center py-3 px-4 rounded-t-lg text-lg font-bold">
                            Top Product
                        </div>
                        <div className="flex flex-col items-center p-4">
                            {metrics.topProduct ? (
                                <>
                                    <div className="text-xl font-bold text-orange-600 my-2">
                                        {metrics.topProduct.name}
                                    </div>
                                    <p className="text-sm text-gray-500">
                                        {metrics.topProduct.count} cases
                                    </p>
                                </>
                            ) : (
                                <p className="text-gray-500">No data available</p>
                            )}
                        </div>
                    </div>
                </div>

                {/* Product Distribution Chart */}
                <div className="bg-white rounded-xl shadow-lg mb-6">
                    <div className="bg-gradient-to-r from-blue-700 to-indigo-900 text-white text-center py-3 px-4 rounded-t-lg text-lg font-bold">
                        Product Distribution
                    </div>
                    <div className="p-4">
                        <div className="h-96 w-full">
                            {metrics.distributionData.length > 0 ? (
                                <ResponsiveContainer width="100%" height="100%">
                                    <BarChart data={metrics.distributionData}>
                                        <XAxis dataKey="name" />
                                        <YAxis />
                                        <Tooltip content={<CustomTooltip />} />
                                        <Bar dataKey="value" fill="#4f46e5" radius={[4, 4, 0, 0]} />
                                    </BarChart>
                                </ResponsiveContainer>
                            ) : (
                                <div className="flex h-full justify-center items-center text-gray-500">
                                    No data available
                                </div>
                            )}
                        </div>
                    </div>
                </div>

                {/* Data Table */}
                <div className="bg-white rounded-xl shadow-lg overflow-hidden">
                    <div className="bg-gradient-to-r from-blue-700 to-indigo-900 text-white text-center py-3 px-4 rounded-t-lg text-lg font-bold">
                        Case Details
                    </div>
                    <div className="p-4 overflow-x-auto">
                        <table className="min-w-full divide-y divide-gray-200">
                            <thead className="bg-gray-50">
                                <tr>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Product</th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Sub Product</th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Problem</th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Root Cause</th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">AHT</th>
                                </tr>
                            </thead>
                            <tbody className="bg-white divide-y divide-gray-200">
                                {filteredData
                                    .slice(page * rowsPerPage, (page + 1) * rowsPerPage)
                                    .map((row, index) => (
                                        <tr key={index} className="hover:bg-gray-50 transition-colors">
                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{row.Products || ''}</td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{row['Sub Product'] || ''}</td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{row.Problem || ''}</td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{row['Root cause'] || ''}</td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{row.AHT || ''}</td>
                                        </tr>
                                    ))}
                            </tbody>
                        </table>

                        {/* Pagination */}
                        <div className="flex items-center justify-between border-t border-gray-200 bg-white py-3">
                            <div className="flex flex-1 items-center justify-between">
                                <div>
                                    <p className="text-sm text-gray-700">
                                        Showing <span className="font-medium">{page * rowsPerPage + 1}</span> to{' '}
                                        <span className="font-medium">
                                            {Math.min((page + 1) * rowsPerPage, filteredData.length)}
                                        </span>{' '}
                                        of <span className="font-medium">{filteredData.length}</span> results
                                    </p>
                                </div>
                                <div className="flex">
                                    <select
                                        className="mr-4 border border-gray-300 rounded-md text-sm"
                                        value={rowsPerPage}
                                        onChange={handleChangeRowsPerPage}
                                    >
                                        {[10, 20, 30].map((value) => (
                                            <option key={value} value={value}>
                                                {value} rows
                                            </option>
                                        ))}
                                    </select>
                                    <div>
                                        <button
                                            onClick={() => handleChangePage(null, page - 1)}
                                            disabled={page === 0}
                                            className={`relative inline-flex items-center px-2 py-1 rounded-l-md border ${page === 0 ? 'border-gray-300 bg-gray-100 text-gray-400' : 'border-gray-300 bg-white text-gray-700 hover:bg-gray-50'
                                                }`}
                                        >
                                            Previous
                                        </button>
                                        <button
                                            onClick={() => handleChangePage(null, page + 1)}
                                            disabled={page >= Math.ceil(filteredData.length / rowsPerPage) - 1}
                                            className={`relative inline-flex items-center px-2 py-1 rounded-r-md border ${page >= Math.ceil(filteredData.length / rowsPerPage) - 1
                                                ? 'border-gray-300 bg-gray-100 text-gray-400'
                                                : 'border-gray-300 bg-white text-gray-700 hover:bg-gray-50'
                                                }`}
                                        >
                                            Next
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Products;