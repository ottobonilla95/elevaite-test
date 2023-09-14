/* eslint-disable react-hooks/exhaustive-deps */
/* eslint-disable @next/next/no-img-element */
import React, { useEffect } from "react";
import Box from "@mui/material/Box";
import InputLabel from "@mui/material/InputLabel";
import MenuItem from "@mui/material/MenuItem";
import FormControl from "@mui/material/FormControl";
import Select, { SelectChangeEvent } from "@mui/material/Select";

export enum Collections {
  Netgear = "netgear",
  Netskope = "netskope",
  PAN = "pan",
  Cisco = "cisco",
  Cisco_CLO = "cisco_clo"
}



export default function SubHeader(props: any) {
  const [tenant, setTenant] = React.useState<string>(Collections.Cisco_CLO);
  const handleTenantChange = (event: SelectChangeEvent) => {
    props.updateCollection(event.target.value as string);
    setTenant(() => event.target.value as string);
  };

  return (
    <div className="subheader">
      <div className="frame-1000004668 frame">
        <div className="workbench">Gen-AI Bot</div>
      </div>
      <div style={{ marginTop: 5 }}>
        <Box sx={{ minWidth: 120 }}>
          <FormControl style={{ color: "white" }} fullWidth>
            <InputLabel
              style={{ color: "white" }}
              id="demo-simple-select-label"
            >
              Tenant
            </InputLabel>
            <Select
              style={{ color: "white" }}
              labelId="demo-simple-select-label"
              id="demo-simple-select"
              value={tenant}
              label="Tenant"
              onChange={handleTenantChange}
            >
              <MenuItem value={Collections.Netgear}>Network Devices Provider</MenuItem>
              <MenuItem value={Collections.Netskope}>Edge Security Provider</MenuItem>
              <MenuItem value={Collections.PAN}>Hardware Firewall Provider</MenuItem>
              <MenuItem value={Collections.Cisco}>Collaboration Provider</MenuItem>
              <MenuItem value={Collections.Cisco_CLO}>CLO</MenuItem>
              {/* <MenuItem value={Collections.Netgear}>Netgear</MenuItem> */}
            </Select>
          </FormControl>
        </Box>
      </div>
    </div>
  );
}
