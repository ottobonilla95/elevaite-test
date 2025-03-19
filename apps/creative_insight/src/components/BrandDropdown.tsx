// components/BrandDropdown.tsx
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
  } from "./ui/select";
import { useEffect } from "react";
  interface BrandDropdownProps {
    brands: string[];
    selectedBrand: string;
    setSelectedBrand: (value: string) => void;
    setSelectedCampaign: (value: string) => void;
    setSelectedAdSurface: (value: string) => void;
  }
  
  const BrandDropdown = ({
    brands,
    selectedBrand,
    setSelectedBrand,
    setSelectedCampaign,
    setSelectedAdSurface
  }: BrandDropdownProps) => {

    const handleBrandChange = (value: string) => {
      setSelectedBrand(value);
      setSelectedAdSurface(""); // Reset adSurface
      setSelectedCampaign(""); // Reset campaign
    };

    return (
      <div className="space-y-2">
      <label className="text-sm font-medium block ml-2 hover:brandyellow" htmlFor="brandSelect" >
        Brand
      </label>
      <Select onValueChange={handleBrandChange}>
        <SelectTrigger className="w-[180px]" id="brandSelect">
          <SelectValue placeholder="Select a Brand" />
        </SelectTrigger>
        <SelectContent>
          {brands.map((brand) => (
            <SelectItem key={brand} value={brand}>
              {brand}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      </div>
    );
  };
  
  export default BrandDropdown;
  