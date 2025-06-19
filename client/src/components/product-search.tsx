import { useState, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { Input } from "@/components/ui/input";
import { Search } from "lucide-react";
import { Product } from "@shared/schema";
import { API_BASE_URL } from "@/config";

interface ProductSearchProps {
  onSelectProduct: (productId: number) => void;
}

export default function ProductSearch({ onSelectProduct }: ProductSearchProps) {
  const [query, setQuery] = useState("");
  const [showResults, setShowResults] = useState(false);

  const { data: searchResults = [] } = useQuery<Product[]>({
    queryKey: ['/products/search', query],
    queryFn: async () => {
      if (query.length < 2) return [];
      const response = await fetch(
        `${API_BASE_URL}/products/search?q=${encodeURIComponent(query)}`,
      );
      if (!response.ok) throw new Error('Search failed');
      return response.json();
    },
    enabled: query.length >= 2,
  });

  useEffect(() => {
    setShowResults(query.length >= 2 && searchResults.length > 0);
  }, [query, searchResults]);

  const handleSelectProduct = (product: Product) => {
    onSelectProduct(product.id);
    setQuery(product.product_name);
    setShowResults(false);
  };

  return (
    <div className="relative">
      <div className="relative">
        <Input
          type="text"
          placeholder="Search products by name, code, or brand..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => query.length >= 2 && setShowResults(true)}
          className="w-full pl-10 pr-4 py-2"
        />
        <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
      </div>
      
      {showResults && (
        <div className="absolute top-full left-0 right-0 bg-white border border-gray-200 rounded-lg shadow-lg mt-1 max-h-60 overflow-y-auto z-50">
          {searchResults.map((product) => (
            <div
              key={product.id}
              className="p-3 hover:bg-gray-50 cursor-pointer border-b border-gray-100 last:border-b-0"
              onClick={() => handleSelectProduct(product)}
            >
              <div className="font-medium text-gray-900">{product.product_name}</div>
              <div className="text-sm text-gray-500">{product.product_code}</div>
              <div className="text-sm text-gray-600">{product.brand_name}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
