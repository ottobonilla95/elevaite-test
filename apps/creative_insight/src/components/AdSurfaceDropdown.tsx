"use client";

import * as React from "react";
import { cn } from "@/lib/utils";
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandSeparator,
} from "@/components/ui/command";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";

interface AdSurfaceDropdownProps {
  adSurfaces: string[];
  selectedAdSurface: string;
  setSelectedAdSurface: (value: string) => void;
  setSelectedBrand: (value: string) => void;
  setSelectedCampaign: (value: string) => void;
}

export function AdSurfaceDropdown({
  adSurfaces,
  selectedAdSurface,
  setSelectedAdSurface,
  setSelectedBrand,
  setSelectedCampaign,
}: AdSurfaceDropdownProps) {
  const [open, setOpen] = React.useState(false);

  return (
    <div className="space-y-2">
      {/* Label for the dropdown */}
      <label className="text-sm  block ml-2">
      Ad Surface
      </label>
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger className="relative">
        <div
          role="combobox"
          aria-expanded={open}
          className={cn(
            "flex h-9 w-[180px] items-center justify-between rounded-md border border-input  px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 cursor-pointer",
            !selectedAdSurface && "text-muted-foreground"
          )}
          onClick={() => setOpen((prev) => !prev)} // Toggle dropdown visibility
        >
          {selectedAdSurface
            ? adSurfaces.find((surface) => surface === selectedAdSurface)
            : "Select Ad Surface"}
        </div>
      </PopoverTrigger >
      <PopoverContent className="w-[200px] p-0">
        <Command>
          <CommandInput placeholder="Search ad surface..." />
          <CommandList>
            <CommandEmpty>No ad surface found.</CommandEmpty>
            <CommandGroup>
              {adSurfaces.map((surface) => (
                <CommandItem
                  key={surface}
                  value={surface}
                  onSelect={(currentValue) => {
                    setSelectedAdSurface(currentValue);
                    setSelectedBrand("");
                    setSelectedCampaign("");
                    setOpen(false);
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
