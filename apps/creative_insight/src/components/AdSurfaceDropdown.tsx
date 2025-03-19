import * as React from "react";
import { cn } from "../lib/utils"; // Will need to configure in the future
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandSeparator,
} from "./ui/command";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "./ui/popover";
import { useState, useEffect } from "react";

interface AdSurfaceDropdownProps {
  filteredAdSurfaces: string[];
  selectedAdSurface: string;
  setSelectedAdSurface: (value: string) => void;
  selectedBrand: string;
  setSelectedCampaign: (value: string)=> void;
}

export function AdSurfaceDropdown({
  filteredAdSurfaces,
  selectedAdSurface,
  setSelectedAdSurface,
  selectedBrand,
  setSelectedCampaign
}: AdSurfaceDropdownProps) {
  const [open, setOpen] = useState(false);

  useEffect(() => {
    if (!selectedBrand){
    setSelectedAdSurface("");
  }
  },[selectedBrand,setSelectedAdSurface]);

  const handleAdSurfaceChange = (value: string) => {
    setSelectedCampaign(""); // Clear selectedCampaign
    setSelectedAdSurface(value);
  };
  // Toggles the popover open/close when clicking on the dropdown button.
  const handlePopoverToggle = () => {
    setOpen((prev) => !prev);
  };
  
  return (
    <div className="space-y-2">
      {/* <label className="text-sm font-medium block ml-2">Ad Surface</label> */}
      <label htmlFor="adSurfaceTrigger" className="text-sm font-medium block ml-2">
        Ad Surface
      </label>

      <Popover open={open} onOpenChange={setOpen}>
        <PopoverTrigger  id="adSurfaceTrigger" className="relative focus:outline-none focus:ring-1 focus:ring-ring rounded-md hover:outline-none hover:ring-1 hover:ring-ring data-[state=open]:outline-none data-[state=open]:ring-1 data-[state=open]:ring-ring">
          <div
            role="combobox"
            onKeyDown={(e) => {
              if (e.key === "Enter" || e.key === " ") {
                handlePopoverToggle();
              }
            }}
            tabIndex={0}
            aria-controls="ad-surface-list"
            aria-expanded={open ? "true" : "false"}
            className={cn(
              "flex h-9 w-[180px] items-center justify-between rounded-md border border-input px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground  cursor-pointer ",
              !selectedAdSurface && "text-muted-foreground"   
            )}
            onClick={handlePopoverToggle} // Toggle the dropdown visibility
          >
            {selectedAdSurface
              ? filteredAdSurfaces.find((surface) => surface === selectedAdSurface)
              : "Select Ad Surface"}
          </div>
        </PopoverTrigger>
        <PopoverContent id="ad-surface-list" className="w-[200px] p-0">
          <Command>
            <CommandInput placeholder="Search ad surface..." />
            <CommandList>
              <CommandEmpty>No ad surface found.</CommandEmpty>
              <CommandGroup>
                {filteredAdSurfaces.map((surface) => (
                  <CommandItem
                    key={surface}
                    value={surface}
                    onSelect={() => {
                      handleAdSurfaceChange(surface); // Set the selected ad surface
                      setOpen(false); // Close the popover after selection
                    }}
                  >
                    {surface}
                  </CommandItem>
                ))}
              </CommandGroup>
              <CommandSeparator />
            </CommandList>
          </Command>
        </PopoverContent>
      </Popover>
    </div>
  );
}
