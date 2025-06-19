import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { ProductAnalytics, OverallAnalytics } from "@shared/schema";

export default function Analytics() {
  const currentMonth = new Date().toISOString().slice(0, 7); // YYYY-MM format

  const { data: overallAnalytics, isLoading: overallLoading } = useQuery<OverallAnalytics>({
    queryKey: ['/analytics/overall', currentMonth],
  });

  const { data: productAnalytics = [], isLoading: productLoading } = useQuery<ProductAnalytics[]>({
    queryKey: ['/analytics/products', currentMonth],
  });

  if (overallLoading || productLoading) {
    return (
      <div className="p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-4 bg-gray-200 rounded w-1/4"></div>
          <div className="h-32 bg-gray-200 rounded"></div>
          <div className="h-64 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      {/* Analytics Header */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Sales Analytics & Performance</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div className="text-center">
              <div className="text-3xl font-bold text-primary">
                {overallAnalytics?.total_sell_in || 0}
              </div>
              <div className="text-sm text-gray-500">Total Sell-In (This Month)</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-success">
                {overallAnalytics?.total_sell_through || 0}
              </div>
              <div className="text-sm text-gray-500">Total Sell-Through (This Month)</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-warning">
                {overallAnalytics?.average_turnover_rate || 0}%
              </div>
              <div className="text-sm text-gray-500">Average Turnover Rate</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-gray-900">
                ${overallAnalytics?.total_revenue?.toLocaleString() || '0'}
              </div>
              <div className="text-sm text-gray-500">Total Revenue</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Top Performing Products */}
      <Card>
        <CardHeader>
          <CardTitle>Top Performing Products</CardTitle>
        </CardHeader>
        <CardContent>
          {productAnalytics.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              No sales data available for this month
            </div>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Product</TableHead>
                    <TableHead>Sell-In</TableHead>
                    <TableHead>Sell-Through</TableHead>
                    <TableHead>Turnover %</TableHead>
                    <TableHead>Revenue</TableHead>
                    <TableHead>Current Stock</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {productAnalytics.map((product) => (
                    <TableRow key={product.product_id}>
                      <TableCell>
                        <div>
                          <div className="font-medium text-gray-900">{product.product_name}</div>
                          <div className="text-sm text-gray-500">{product.product_code}</div>
                          <div className="text-sm text-gray-600">{product.brand_name}</div>
                        </div>
                      </TableCell>
                      <TableCell>{product.sell_in_quantity}</TableCell>
                      <TableCell>{product.sell_through_quantity}</TableCell>
                      <TableCell>
                        <Badge 
                          variant={product.turnover_rate >= 80 ? 'default' : product.turnover_rate >= 50 ? 'secondary' : 'destructive'}
                        >
                          {product.turnover_rate}%
                        </Badge>
                      </TableCell>
                      <TableCell>${product.total_revenue.toLocaleString()}</TableCell>
                      <TableCell>
                        <span className={product.current_stock < 5 ? 'text-red-600 font-medium' : ''}>
                          {product.current_stock}
                        </span>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
