import { useState, useEffect } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Checkbox } from "@/components/ui/checkbox";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Save, Edit, Camera, ChevronDown, ChevronUp } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { Product, ProductAnalytics } from "@shared/schema";
import { apiRequest } from "@/lib/queryClient";
import { queryClient } from "@/lib/queryClient";

interface ProductDetailsProps {
  productId: number | null;
}

export default function ProductDetails({ productId }: ProductDetailsProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [showAllAttributes, setShowAllAttributes] = useState(false);
  const [formData, setFormData] = useState<Product | null>(null);
  const { toast } = useToast();

  const { data: product, isLoading } = useQuery<Product>({
    queryKey: ['/products', productId],
    enabled: !!productId,
  });

  const { data: analytics } = useQuery<ProductAnalytics[]>({
    queryKey: ['/analytics/products', productId],
    enabled: !!productId,
  });

  const updateMutation = useMutation({
    mutationFn: async (data: Partial<Product>) => {
      if (!productId) throw new Error('No product ID');
      return apiRequest('PUT', `/products/${productId}`, data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['/products'] });
      queryClient.invalidateQueries({ queryKey: ['/products', productId] });
      setIsEditing(false);
      toast({
        title: "Success",
        description: "Product updated successfully",
      });
    },
    onError: () => {
      toast({
        title: "Error",
        description: "Failed to update product",
        variant: "destructive",
      });
    },
  });

  useEffect(() => {
    if (product) {
      setFormData(product);
    }
  }, [product]);

  useEffect(() => {
    if (isEditing) {
      setShowAllAttributes(true);
    }
  }, [isEditing]);

  if (!productId) {
    return (
      <div className="p-6 text-center">
        <p className="text-gray-500">Select a product from the search to view details</p>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-4 bg-gray-200 rounded w-1/4"></div>
          <div className="h-4 bg-gray-200 rounded w-1/2"></div>
          <div className="h-4 bg-gray-200 rounded w-3/4"></div>
        </div>
      </div>
    );
  }

  if (!formData) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    updateMutation.mutate(formData);
  };

  const handleInputChange = (field: keyof Product, value: any) => {
    setFormData(prev => prev ? { ...prev, [field]: value } : null);
  };

  const calculateMarginDetails = (sellPriceIncl: string, costPriceIncl: string) => {
    const sellPrice = parseFloat(sellPriceIncl || '0');
    const costPrice = parseFloat(costPriceIncl || '0');
    
    if (costPrice === 0) return { 
      grossMarginPercentage: 0, 
      markupPercentage: 0, 
      grossProfit: 0,
      sellPriceExcl: 0,
      costPriceExcl: 0
    };

    // GST calculations (10% GST)
    const gstRate = 0.10;
    const sellPriceExcl = sellPrice / (1 + gstRate);
    const costPriceExcl = costPrice / (1 + gstRate);
    
    const grossProfit = sellPrice - costPrice;
    const grossMarginPercentage = (grossProfit / sellPrice) * 100;
    const markupPercentage = (grossProfit / costPrice) * 100;
    
    return { 
      grossMarginPercentage: Math.round(grossMarginPercentage * 100) / 100, 
      markupPercentage: Math.round(markupPercentage * 100) / 100, 
      grossProfit: Math.round(grossProfit * 100) / 100,
      sellPriceExcl: Math.round(sellPriceExcl * 100) / 100,
      costPriceExcl: Math.round(costPriceExcl * 100) / 100
    };
  };

  // Franchise level calculations (RRP vs Trade)
  const franchiseMargin = calculateMarginDetails(formData.rrp || '0', formData.trade || '0');
  
  // Store level calculations (MWP vs Trade, GO vs Trade)
  const mwpStoreMargin = calculateMarginDetails(formData.mwp || '0', formData.trade || '0');
  const goStoreMargin = calculateMarginDetails(formData.go || '0', formData.trade || '0');

  const productAnalytics = analytics?.[0];

  return (
    <div className="p-6">
      <form onSubmit={handleSubmit}>
        {/* Product Overview Card */}
        <Card className="mb-6">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Product Overview</CardTitle>
              <div className="flex items-center space-x-2">
                <Badge variant={formData.status === 'Active' ? 'default' : 'secondary'}>
                  {formData.status}
                </Badge>
                <div className="flex items-center space-x-2">
                  {!isEditing && (
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      onClick={() => setShowAllAttributes(!showAllAttributes)}
                    >
                      {showAllAttributes ? (
                        <>
                          <ChevronUp className="h-4 w-4 mr-1" />
                          Hide Attributes
                        </>
                      ) : (
                        <>
                          <ChevronDown className="h-4 w-4 mr-1" />
                          Show All Attributes
                        </>
                      )}
                    </Button>
                  )}
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => setIsEditing(!isEditing)}
                  >
                    <Edit className="h-4 w-4 mr-2" />
                    {isEditing ? 'Cancel' : 'Edit Product'}
                  </Button>
                </div>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Product Image */}
              <div className="lg:col-span-1">
                <img 
                  src="https://images.unsplash.com/photo-1593359677879-a4bb92f829d1?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&h=300" 
                  alt="Product" 
                  className="w-full h-48 object-cover rounded-lg border border-gray-200"
                />
                {isEditing && (
                  <Button type="button" variant="ghost" size="sm" className="mt-2 w-full">
                    <Camera className="h-4 w-4 mr-1" />
                    Update Image
                  </Button>
                )}
              </div>
              
              {/* Product Basic Info */}
              <div className="lg:col-span-2">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="product_name">Product Name</Label>
                    <Input
                      id="product_name"
                      value={formData.product_name || ''}
                      onChange={(e) => handleInputChange('product_name', e.target.value)}
                      disabled={!isEditing}
                    />
                  </div>
                  <div>
                    <Label htmlFor="product_code">Product Code</Label>
                    <Input
                      id="product_code"
                      value={formData.product_code || ''}
                      onChange={(e) => handleInputChange('product_code', e.target.value)}
                      disabled={!isEditing}
                    />
                  </div>
                  <div>
                    <Label htmlFor="brand_name">Brand Name</Label>
                    <Input
                      id="brand_name"
                      value={formData.brand_name || ''}
                      onChange={(e) => handleInputChange('brand_name', e.target.value)}
                      disabled={!isEditing}
                    />
                  </div>
                  <div>
                    <Label htmlFor="product_secondary_code">Secondary Code</Label>
                    <Input
                      id="product_secondary_code"
                      value={formData.product_secondary_code || ''}
                      onChange={(e) => handleInputChange('product_secondary_code', e.target.value)}
                      disabled={!isEditing}
                    />
                  </div>
                  <div>
                    <Label htmlFor="distributor_name">Distributor</Label>
                    <Select
                      value={formData.distributor_name || ''}
                      onValueChange={(value) => handleInputChange('distributor_name', value)}
                      disabled={!isEditing}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="Samsung Electronics">Samsung Electronics</SelectItem>
                        <SelectItem value="Tech Distributors Ltd">Tech Distributors Ltd</SelectItem>
                        <SelectItem value="Electronics Wholesale Co">Electronics Wholesale Co</SelectItem>
                        <SelectItem value="Beko">Beko</SelectItem>
                        <SelectItem value="LG Electronics">LG Electronics</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label htmlFor="ean">EAN</Label>
                    <Input
                      id="ean"
                      value={formData.ean || ''}
                      onChange={(e) => handleInputChange('ean', e.target.value)}
                      disabled={!isEditing}
                    />
                  </div>
                </div>
              </div>
            </div>

            {/* Additional Attributes - Conditionally Displayed */}
            {(showAllAttributes || isEditing) && (
              <div className="mt-8 pt-6 border-t border-gray-200">
                <h4 className="text-md font-medium text-gray-900 mb-4">Additional Product Attributes</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <Label htmlFor="status">Product Status</Label>
                    <Select
                      value={formData.status || ''}
                      onValueChange={(value) => handleInputChange('status', value)}
                      disabled={!isEditing}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="Active">Active</SelectItem>
                        <SelectItem value="Inactive">Inactive</SelectItem>
                        <SelectItem value="Discontinued">Discontinued</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label htmlFor="superceded_by">Superseded By</Label>
                    <Input
                      id="superceded_by"
                      value={formData.superceded_by || ''}
                      onChange={(e) => handleInputChange('superceded_by', e.target.value)}
                      disabled={!isEditing}
                      placeholder="Enter product code if applicable"
                    />
                  </div>
                  <div>
                    <Label htmlFor="web_title">Web Title</Label>
                    <Input
                      id="web_title"
                      value={formData.web_title || ''}
                      onChange={(e) => handleInputChange('web_title', e.target.value)}
                      disabled={!isEditing}
                    />
                  </div>
                  <div>
                    <Label htmlFor="hyperlink">Product Link</Label>
                    <Input
                      id="hyperlink"
                      type="url"
                      value={formData.hyperlink || ''}
                      onChange={(e) => handleInputChange('hyperlink', e.target.value)}
                      disabled={!isEditing}
                      placeholder="https://..."
                    />
                  </div>
                  <div>
                    <Label htmlFor="features_and_benefits_codes">Features & Benefits</Label>
                    <Input
                      id="features_and_benefits_codes"
                      value={formData.features_and_benefits_codes || ''}
                      onChange={(e) => handleInputChange('features_and_benefits_codes', e.target.value)}
                      disabled={!isEditing}
                      placeholder="Comma-separated codes"
                    />
                  </div>
                  <div>
                    <Label htmlFor="badges_codes">Badge Codes</Label>
                    <Input
                      id="badges_codes"
                      value={formData.badges_codes || ''}
                      onChange={(e) => handleInputChange('badges_codes', e.target.value)}
                      disabled={!isEditing}
                      placeholder="Comma-separated codes"
                    />
                  </div>
                  <div>
                    <Label htmlFor="category_name">Category</Label>
                    <Select
                      value={formData.category_name || ''}
                      onValueChange={(value) => handleInputChange('category_name', value)}
                      disabled={!isEditing}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="Television & Audio">Television & Audio</SelectItem>
                        <SelectItem value="Home Appliances">Home Appliances</SelectItem>
                        <SelectItem value="Mobile & Accessories">Mobile & Accessories</SelectItem>
                        <SelectItem value="Computing">Computing</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label htmlFor="shipping_class">Shipping Class</Label>
                    <Select
                      value={formData.shipping_class || ''}
                      onValueChange={(value) => handleInputChange('shipping_class', value)}
                      disabled={!isEditing}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="Large Items">Large Items</SelectItem>
                        <SelectItem value="Standard">Standard</SelectItem>
                        <SelectItem value="Express">Express</SelectItem>
                        <SelectItem value="Fragile">Fragile</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label htmlFor="pack_size">Pack Size</Label>
                    <Input
                      id="pack_size"
                      type="number"
                      value={formData.pack_size || 1}
                      onChange={(e) => handleInputChange('pack_size', parseInt(e.target.value))}
                      disabled={!isEditing}
                    />
                  </div>
                  <div>
                    <Label htmlFor="core_group">Core Group</Label>
                    <Input
                      id="core_group"
                      value={formData.core_group || ''}
                      onChange={(e) => handleInputChange('core_group', e.target.value)}
                      disabled={!isEditing}
                    />
                  </div>
                  <div>
                    <Label htmlFor="product_availability">Availability Status</Label>
                    <Select
                      value={formData.product_availability || ''}
                      onValueChange={(value) => handleInputChange('product_availability', value)}
                      disabled={!isEditing}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="In Stock">In Stock</SelectItem>
                        <SelectItem value="Low Stock">Low Stock</SelectItem>
                        <SelectItem value="Out of Stock">Out of Stock</SelectItem>
                        <SelectItem value="Discontinued">Discontinued</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div className="mt-6">
                  <Label htmlFor="description">Product Description</Label>
                  <Textarea
                    id="description"
                    rows={3}
                    value={formData.description || ''}
                    onChange={(e) => handleInputChange('description', e.target.value)}
                    disabled={!isEditing}
                    placeholder="Detailed product description..."
                  />
                </div>

                <div className="mt-6">
                  <Label htmlFor="summary">Product Summary</Label>
                  <Textarea
                    id="summary"
                    rows={2}
                    value={formData.summary || ''}
                    onChange={(e) => handleInputChange('summary', e.target.value)}
                    disabled={!isEditing}
                    placeholder="Brief product summary..."
                  />
                </div>

                {/* Boolean Flags */}
                <div className="mt-6">
                  <h4 className="text-sm font-medium text-gray-900 mb-4">Product Settings</h4>
                  <div className="flex flex-wrap gap-6">
                    <div className="flex items-center space-x-2">
                      <Checkbox
                        id="online"
                        checked={formData.online || false}
                        onCheckedChange={(checked) => handleInputChange('online', checked)}
                        disabled={!isEditing}
                      />
                      <Label htmlFor="online">Available Online</Label>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Checkbox
                        id="tax_exmt"
                        checked={formData.tax_exmt || false}
                        onCheckedChange={(checked) => handleInputChange('tax_exmt', checked)}
                        disabled={!isEditing}
                      />
                      <Label htmlFor="tax_exmt">Tax Exempt</Label>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Checkbox
                        id="stock_unmanaged"
                        checked={formData.stock_unmanaged || false}
                        onCheckedChange={(checked) => handleInputChange('stock_unmanaged', checked)}
                        disabled={!isEditing}
                      />
                      <Label htmlFor="stock_unmanaged">Unmanaged Stock</Label>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Pricing & Margin Card */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Pricing & Margins</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              <div>
                <Label htmlFor="trade">Trade Price</Label>
                <div className="relative">
                  <span className="absolute left-3 top-2 text-gray-500">$</span>
                  <Input
                    id="trade"
                    type="number"
                    step="0.01"
                    value={formData.trade || ''}
                    onChange={(e) => handleInputChange('trade', e.target.value)}
                    disabled={!isEditing}
                    className="pl-8"
                  />
                </div>
              </div>
              <div>
                <Label htmlFor="rrp">RRP</Label>
                <div className="relative">
                  <span className="absolute left-3 top-2 text-gray-500">$</span>
                  <Input
                    id="rrp"
                    type="number"
                    step="0.01"
                    value={formData.rrp || ''}
                    onChange={(e) => handleInputChange('rrp', e.target.value)}
                    disabled={!isEditing}
                    className="pl-8"
                  />
                </div>
              </div>
              <div>
                <Label htmlFor="mwp">MWP</Label>
                <div className="relative">
                  <span className="absolute left-3 top-2 text-gray-500">$</span>
                  <Input
                    id="mwp"
                    type="number"
                    step="0.01"
                    value={formData.mwp || ''}
                    onChange={(e) => handleInputChange('mwp', e.target.value)}
                    disabled={!isEditing}
                    className="pl-8"
                  />
                </div>
              </div>
              <div>
                <Label htmlFor="go">GO Price</Label>
                <div className="relative">
                  <span className="absolute left-3 top-2 text-gray-500">$</span>
                  <Input
                    id="go"
                    type="number"
                    step="0.01"
                    value={formData.go || ''}
                    onChange={(e) => handleInputChange('go', e.target.value)}
                    disabled={!isEditing}
                    className="pl-8"
                  />
                </div>
              </div>
            </div>
            
            {/* Enhanced Margin Calculators */}
            <div className="mt-8 space-y-6">
              {/* Franchise Level Margin Calculator */}
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
                <h4 className="text-lg font-semibold text-blue-900 mb-4">Franchise Level - Margin Calculator (Incl. GST)</h4>
                <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                  <div className="text-center">
                    <div className="text-sm text-blue-600 font-medium">Sell Price (incl.)</div>
                    <div className="text-xl font-bold text-blue-800">${parseFloat(formData.rrp || '0').toFixed(2)}</div>
                  </div>
                  <div className="text-center">
                    <div className="text-sm text-blue-600 font-medium">Net Cost (incl.)</div>
                    <div className="text-xl font-bold text-blue-800">${parseFloat(formData.trade || '0').toFixed(2)}</div>
                  </div>
                  <div className="text-center">
                    <div className="text-sm text-blue-600 font-medium">Gross Margin</div>
                    <div className="text-xl font-bold text-blue-800">{franchiseMargin.grossMarginPercentage}%</div>
                  </div>
                  <div className="text-center">
                    <div className="text-sm text-blue-600 font-medium">Markup</div>
                    <div className="text-xl font-bold text-blue-800">{franchiseMargin.markupPercentage}%</div>
                  </div>
                  <div className="text-center">
                    <div className="text-sm text-blue-600 font-medium">Gross Profit (incl.)</div>
                    <div className="text-xl font-bold text-blue-800">${franchiseMargin.grossProfit}</div>
                  </div>
                </div>
                <div className="mt-4 pt-4 border-t border-blue-200">
                  <div className="grid grid-cols-2 gap-4 text-sm text-blue-700">
                    <div>Sell Price (excl. GST): ${franchiseMargin.sellPriceExcl}</div>
                    <div>Net Cost (excl. GST): ${franchiseMargin.costPriceExcl}</div>
                  </div>
                </div>
              </div>

              {/* Store Level Margin Calculators */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* MWP Store Level */}
                <div className="bg-green-50 border border-green-200 rounded-lg p-6">
                  <h4 className="text-lg font-semibold text-green-900 mb-4">Store Level (MWP) - Margin Calculator</h4>
                  <div className="space-y-3">
                    <div className="flex justify-between">
                      <span className="text-sm text-green-600 font-medium">Sell Price (incl.):</span>
                      <span className="font-bold text-green-800">${parseFloat(formData.mwp || '0').toFixed(2)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-green-600 font-medium">Net Cost (incl.):</span>
                      <span className="font-bold text-green-800">${parseFloat(formData.trade || '0').toFixed(2)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-green-600 font-medium">Gross Margin:</span>
                      <span className="font-bold text-green-800">{mwpStoreMargin.grossMarginPercentage}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-green-600 font-medium">Markup:</span>
                      <span className="font-bold text-green-800">{mwpStoreMargin.markupPercentage}%</span>
                    </div>
                    <div className="flex justify-between border-t border-green-200 pt-2">
                      <span className="text-sm text-green-600 font-medium">Gross Profit (incl.):</span>
                      <span className="font-bold text-green-800">${mwpStoreMargin.grossProfit}</span>
                    </div>
                  </div>
                </div>

                {/* GO Store Level */}
                <div className="bg-orange-50 border border-orange-200 rounded-lg p-6">
                  <h4 className="text-lg font-semibold text-orange-900 mb-4">Store Level (GO) - Margin Calculator</h4>
                  <div className="space-y-3">
                    <div className="flex justify-between">
                      <span className="text-sm text-orange-600 font-medium">Sell Price (incl.):</span>
                      <span className="font-bold text-orange-800">${parseFloat(formData.go || '0').toFixed(2)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-orange-600 font-medium">Net Cost (incl.):</span>
                      <span className="font-bold text-orange-800">${parseFloat(formData.trade || '0').toFixed(2)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-orange-600 font-medium">Gross Margin:</span>
                      <span className="font-bold text-orange-800">{goStoreMargin.grossMarginPercentage}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-orange-600 font-medium">Markup:</span>
                      <span className="font-bold text-orange-800">{goStoreMargin.markupPercentage}%</span>
                    </div>
                    <div className="flex justify-between border-t border-orange-200 pt-2">
                      <span className="text-sm text-orange-600 font-medium">Gross Profit (incl.):</span>
                      <span className="font-bold text-orange-800">${goStoreMargin.grossProfit}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>





        {/* Sales Performance Card */}
        {productAnalytics && (
          <Card className="mb-6">
            <CardHeader>
              <CardTitle>Sales Performance</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                <div className="text-center">
                  <div className="text-2xl font-bold text-gray-900">{productAnalytics.sell_in_quantity}</div>
                  <div className="text-sm text-gray-500">Total Sell-In (This Month)</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-gray-900">{productAnalytics.sell_through_quantity}</div>
                  <div className="text-sm text-gray-500">Total Sell-Through (This Month)</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-success">{productAnalytics.turnover_rate}%</div>
                  <div className="text-sm text-gray-500">Turnover Rate</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-gray-900">{productAnalytics.current_stock}</div>
                  <div className="text-sm text-gray-500">Current Stock</div>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Save Changes Button */}
        {isEditing && (
          <div className="flex justify-end">
            <Button type="submit" disabled={updateMutation.isPending}>
              <Save className="h-4 w-4 mr-2" />
              {updateMutation.isPending ? 'Saving...' : 'Save Changes'}
            </Button>
          </div>
        )}
      </form>
    </div>
  );
}
