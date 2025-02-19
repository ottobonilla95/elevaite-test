// components/BrandDropdown.tsx
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
  } from "@/components/ui/select";
import { useEffect } from "react";
  interface BrandDropdownProps {
    filteredBrands: string[];
    selectedBrand: string;
    setSelectedBrand: (value: string) => void;
    setSelectedCampaign: (value: string) => void;
    selectedAdSurface: string; // added selectedAdSurface to props
  }
  
  const BrandDropdown = ({
    filteredBrands,
    selectedBrand,
    setSelectedBrand,
    setSelectedCampaign,
    selectedAdSurface,
  }: BrandDropdownProps) => {
    useEffect(() => {
      if (!selectedAdSurface) {
        setSelectedBrand("");  // Reset the brand if no ad surface is selected
      }
    }, [selectedAdSurface, setSelectedBrand]);
    return (
      <div className="space-y-2">
      <label className="text-sm font-medium block ml-2">
        Brand
      </label>
      <Select
        onValueChange={(value) => {
          setSelectedBrand(value);
          setSelectedCampaign("");
        }}
        disabled={!selectedAdSurface} // disabled if no ad surface is selected
      >
        <SelectTrigger className="w-[180px]">
          <SelectValue placeholder="Select a Brand" />
        </SelectTrigger>
        <SelectContent>
          {filteredBrands.map((brand) => (
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
  