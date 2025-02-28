// components/CampaignDropdown.tsx
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
  } from "../components/ui/select";
  
  interface CampaignDropdownProps {
    campaigns: string[];
    selectedCampaign: string;
    setSelectedCampaign: (value: string) => void;
    selectedBrand: string;
    selectedAdSurface: string;
  }
  
  const CampaignDropdown = ({
    campaigns,
    selectedCampaign,
    setSelectedCampaign,
    selectedBrand,
    selectedAdSurface,
  }: CampaignDropdownProps) => {
    return (
      <div className="space-y-2">
      <label className="text-sm font-medium block ml-2">
        Campaign
      </label>

      <Select
        onValueChange={setSelectedCampaign}
        disabled={!selectedAdSurface} // disabled if no brand is selected
      >
        <SelectTrigger className="w-[180px]">
          <SelectValue placeholder="Select a Campaign" />
        </SelectTrigger>
        <SelectContent>
          {campaigns.map((campaign) => (
            <SelectItem key={campaign} value={campaign}>
              {campaign}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      </div>
    );
  };
  
  export default CampaignDropdown;
  