import * as React from "react";
import InputLabel from "@mui/material/InputLabel";
import FormControl from "@mui/material/FormControl";
import Select, { SelectChangeEvent } from "@mui/material/Select";
import Box from "@mui/material/Box";
import MenuItem from "@mui/material/MenuItem";

export enum ChatbotV {
  InWarranty = "in-warranty",
  OutofWarranty = "out-of-warranty",
  AgentAssist = "agent-assist",
  Upsell = "upsell"
}

export default function RowRadioButtonsGroup(props: any) {
  const [chatbotV, setChatbotV] = React.useState<string>(ChatbotV.InWarranty);
  const setChatbotType = (event: SelectChangeEvent) => {
    props.setChatbotType(event.target.value as string);
    setChatbotV(() => event.target.value as string);
  };
  return (
    <Box sx={{ width: 160, height: 30 }}>
      <FormControl
        disabled={props.isDisabled}
        fullWidth
      >
        <InputLabel
          style={{ color: props.isDisabled ? "black": "white", fontSize: "15px" }}
          id="demo-simple-select-label"
        >
          Chatbot Type
        </InputLabel>
        <Select
          style={{ color: "white", fontSize: "15px", padding: 0 }}
          labelId="demo-simple-select-label"
          id="demo-simple-select"
          value={chatbotV}
          label="Chatbot Type"
          onChange={setChatbotType}
        >
          <MenuItem value={ChatbotV.InWarranty}>In Warranty</MenuItem>
          <MenuItem value={ChatbotV.OutofWarranty}>Out of Warranty</MenuItem>
          <MenuItem value={ChatbotV.AgentAssist}>Agent Assist</MenuItem>
          <MenuItem value={ChatbotV.Upsell}>Upsell</MenuItem>
        </Select>
      </FormControl>
    </Box>
  );
}
