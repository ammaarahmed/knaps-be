import { useState, useRef } from "react";
import { useMutation } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { CloudUpload, Download, CheckCircle, Info } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { apiRequest } from "@/lib/queryClient";
import { queryClient } from "@/lib/queryClient";

interface UploadResult {
  success: number;
  errors: number;
  created: any[];
  failed: { row: number; error: string; details?: any }[];
}

export default function BulkUpload() {
  const [uploadResult, setUploadResult] = useState<UploadResult | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { toast } = useToast();

  const uploadMutation = useMutation({
    mutationFn: async (data: any[]) => {
      const response = await apiRequest('POST', '/products/bulk', data);
      return response.json();
    },
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ['/products'] });
      setUploadResult(result);
      toast({
        title: "Upload Complete",
        description: `${result.success} products uploaded successfully, ${result.errors} failed`,
      });
    },
    onError: () => {
      toast({
        title: "Upload Failed",
        description: "Failed to process bulk upload",
        variant: "destructive",
      });
    },
  });

  const handleFileSelect = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const text = e.target?.result as string;
        const lines = text.split('\n').filter(line => line.trim());
        
        if (lines.length < 2) {
          toast({
            title: "Invalid File",
            description: "CSV file must contain at least a header and one data row",
            variant: "destructive",
          });
          return;
        }

        const headers = lines[0].split(',').map(h => h.trim());
        const products = lines.slice(1).map(line => {
          const values = line.split(',').map(v => v.trim());
          const product: any = {};
          
          headers.forEach((header, index) => {
            const value = values[index] || '';
            
            // Handle specific field types
            switch (header) {
              case 'pack_size':
                product[header] = value ? parseInt(value) : 1;
                break;
              case 'online':
              case 'tax_exmt':
              case 'stock_unmanaged':
                product[header] = value.toLowerCase() === 'true' || value === '1';
                break;
              case 'trade':
              case 'rrp':
              case 'mwp':
              case 'go':
                product[header] = value || null;
                break;
              default:
                product[header] = value || null;
            }
          });

          // Set default values
          if (!product.status) product.status = 'Active';
          if (!product.product_availability) product.product_availability = 'In Stock';
          if (product.pack_size === undefined) product.pack_size = 1;
          if (product.online === undefined) product.online = true;
          if (product.tax_exmt === undefined) product.tax_exmt = false;
          if (product.stock_unmanaged === undefined) product.stock_unmanaged = false;

          return product;
        });

        uploadMutation.mutate(products);
      } catch (error) {
        toast({
          title: "File Parse Error",
          description: "Failed to parse CSV file. Please check the format.",
          variant: "destructive",
        });
      }
    };

    reader.readAsText(file);
  };

  const downloadTemplate = () => {
    const headers = [
      'distributor_name',
      'brand_name',
      'product_code',
      'product_secondary_code',
      'product_name',
      'description',
      'summary',
      'shipping_class',
      'category_name',
      'product_availability',
      'status',
      'online',
      'superceded_by',
      'ean',
      'pack_size',
      'mwp',
      'trade',
      'go',
      'rrp',
      'core_group',
      'tax_exmt',
      'hyperlink',
      'web_title',
      'features_and_benefits_codes',
      'badges_codes',
      'stock_unmanaged'
    ];

    const csvContent = [
      headers.join(','),
      // Add a sample row for reference
      'Samsung Electronics,Samsung,SAM-QLED-65-001,QN65Q70A,"Samsung 65\\" QLED 4K Smart TV","Experience stunning picture quality with Samsung\'s QLED technology","65\\" QLED 4K Smart TV with premium display technology",Large Items,Television & Audio,In Stock,Active,true,,1234567890123,1,1199.00,899.00,999.00,1299.00,QLED-TVS,false,https://example.com/samsung-qled-65,"Samsung 65\\" QLED 4K Smart TV - Premium Display Technology","QLED,4K,SMART,HDR","PREMIUM,BESTSELLER",false'
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'product_template.csv';
    a.click();
    window.URL.revokeObjectURL(url);
  };

  return (
    <div className="p-6">
      <Card>
        <CardHeader>
          <CardTitle>Bulk Product Upload</CardTitle>
          <p className="text-sm text-gray-600">Upload multiple products at once using CSV or Excel files.</p>
        </CardHeader>
        <CardContent>
          {/* Upload Area */}
          <div 
            className="border-2 border-dashed border-gray-300 rounded-lg p-12 text-center hover:border-primary transition-colors cursor-pointer"
            onClick={handleFileSelect}
          >
            <CloudUpload className="mx-auto h-12 w-12 text-gray-400 mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">Drop your file here or click to browse</h3>
            <p className="text-sm text-gray-600 mb-4">Supports CSV files up to 10MB</p>
            <Button type="button" disabled={uploadMutation.isPending}>
              {uploadMutation.isPending ? 'Processing...' : 'Select File'}
            </Button>
            <input
              ref={fileInputRef}
              type="file"
              accept=".csv"
              onChange={handleFileChange}
              className="hidden"
            />
          </div>

          {/* Template Download */}
          <Alert className="mt-6 bg-blue-50 border-blue-200">
            <Info className="h-4 w-4 text-blue-600" />
            <AlertDescription>
              <div>
                <h4 className="text-sm font-medium text-blue-900 mb-1">Need a template?</h4>
                <p className="text-sm text-blue-700 mb-2">Download our CSV template to ensure your data is formatted correctly.</p>
                <Button variant="link" className="p-0 h-auto text-blue-600" onClick={downloadTemplate}>
                  <Download className="h-4 w-4 mr-1" />
                  Download Template
                </Button>
              </div>
            </AlertDescription>
          </Alert>

          {/* Field Mapping Preview */}
          <div className="mt-8">
            <h3 className="text-md font-medium text-gray-900 mb-4">Expected CSV Format</h3>
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>distributor_name</TableHead>
                    <TableHead>brand_name</TableHead>
                    <TableHead>product_code</TableHead>
                    <TableHead>product_name</TableHead>
                    <TableHead>trade</TableHead>
                    <TableHead>rrp</TableHead>
                    <TableHead>...</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  <TableRow>
                    <TableCell>Samsung Electronics</TableCell>
                    <TableCell>Samsung</TableCell>
                    <TableCell>SAM-QLED-65</TableCell>
                    <TableCell>Samsung 65" QLED TV</TableCell>
                    <TableCell>899.00</TableCell>
                    <TableCell>1299.00</TableCell>
                    <TableCell className="text-gray-500">...</TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </div>
          </div>

          {/* Upload Status */}
          {uploadResult && (
            <div className="mt-8">
              <Alert className="bg-green-50 border-green-200 mb-4">
                <CheckCircle className="h-4 w-4 text-green-600" />
                <AlertDescription>
                  <div>
                    <h4 className="text-sm font-medium text-green-900 mb-1">Upload Complete</h4>
                    <p className="text-sm text-green-700">
                      {uploadResult.success} products have been successfully imported.
                      {uploadResult.errors > 0 && ` ${uploadResult.errors} products failed to import.`}
                    </p>
                  </div>
                </AlertDescription>
              </Alert>

              {uploadResult.failed.length > 0 && (
                <div>
                  <h4 className="text-sm font-medium text-gray-900 mb-2">Failed Imports</h4>
                  <div className="border rounded-lg overflow-hidden">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Row</TableHead>
                          <TableHead>Error</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {uploadResult.failed.map((failure, index) => (
                          <TableRow key={index}>
                            <TableCell>{failure.row}</TableCell>
                            <TableCell className="text-red-600">{failure.error}</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
