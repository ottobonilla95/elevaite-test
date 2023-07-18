/* eslint-disable react-hooks/exhaustive-deps */
/* eslint-disable @next/next/no-img-element */
import React, { useEffect } from "react";
import Box from "@mui/material/Box";
import InputLabel from "@mui/material/InputLabel";
import MenuItem from "@mui/material/MenuItem";
import FormControl from "@mui/material/FormControl";
import Select, { SelectChangeEvent } from "@mui/material/Select";

export enum Collections {
  Netgear = "kbDocs_netgear_faq",
  Netskope = "kbDocs_netskope_v1",
}



export default function SubHeader(props: any) {
  const [tenant, setTenant] = React.useState<string>(Collections.Netgear);
  const handleTenantChange = (event: SelectChangeEvent) => {
    props.updateCollection(event.target.value as string);
    setTenant(() => event.target.value as string);
  };

  return (
    <div className="subheader">
      <div className="frame-1000004668 frame">
        <div className="workbench">CHATBOT</div>
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
              <MenuItem value={Collections.Netgear}>Netgear</MenuItem>
              {/* <MenuItem value={Collections.Netskope}>Netskope</MenuItem> */}
            </Select>
          </FormControl>
        </Box>
      </div>
    </div>
  );
}
