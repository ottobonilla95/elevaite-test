"use client"
import React, {useState} from "react";
import styles from "./configitem.module.css";
import Box from "@mui/material/Box";
import InputLabel from "@mui/material/InputLabel";
import MenuItem from "@mui/material/MenuItem";
import FormControl from "@mui/material/FormControl";
import Select, { SelectChangeEvent } from "@mui/material/Select";

const ConfigItem = (props:any) => {
  const handleChange = (event: SelectChangeEvent) => {
    props.setValue(event.target.value as string);
  };
  return (
    <div>
      <div className={styles.configItem}>
        <Box sx={{ minWidth: 120 }}>
          <FormControl fullWidth>
            <InputLabel id="demo-simple-select-label">{props.type}</InputLabel>
            <Select
              labelId="demo-simple-select-label"
              id="demo-simple-select"
              value={props.value}
              label={props.type}
              onChange={handleChange}
            >
              {props.options.map((option:any, index:any)=>
                <MenuItem key={index} value={option}>{option}</MenuItem>
              )}
              {/* <MenuItem value={props.options.optionA}>{props.options.optionA}</MenuItem>
              <MenuItem value={props.options.optionB}>{props.options.optionB}</MenuItem>
              <MenuItem value={props.options.optionC}>{props.options.optionC}</MenuItem> */}
            </Select>
          </FormControl>
        </Box>
      </div>
    </div>
  );
};

export default ConfigItem;
