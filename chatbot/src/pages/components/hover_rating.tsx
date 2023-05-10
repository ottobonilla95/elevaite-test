import React, { useState } from "react";
import Rating from "@mui/material/Rating";
import Box from "@mui/material/Box";
import StarIcon from "@mui/icons-material/Star";
import { TbFileExport } from "react-icons/tb";

const labels: { [index: string]: string } = {
  0.5: "Useless",
  1: "Useless",
  1.5: "Poor",
  2: "Poor",
  2.5: "Ok",
  3: "Ok",
  3.5: "Useful",
  4: "Very useful",
  4.5: "Excellent",
  5: "Perfect",
};

function getLabelText(value: number) {
  return `${value} Star${value !== 1 ? "s" : ""}, ${labels[value]}`;
}

function handleClick() {
  // alert("I will send this value to the backend!");
}

export default function HoverRating() {
  const [value, setValue] = useState<number | null>(null);
  const [hover, setHover] = useState(-1);

  return (
    <div className="feedback">
      <Box
        sx={{
          width: 140,
          display: "flex",
          flexDirection:"column",
          color:"white",
          alignItems: "center",
        }}
      >
        <Rating
          name="hover-feedback"
          value={value}
          precision={0.5}
          getLabelText={getLabelText}
          style={{ stroke: "#f46f22" }}
          onChange={(event, newValue) => {
            setValue(newValue);
          }}
          onChangeActive={(event, newHover) => {
            setHover(newHover);
          }}
          onClick={handleClick}
          emptyIcon={<StarIcon style={{ opacity: 0.55 }} fontSize="inherit" />}
        />
        {value !== null && (
        <Box sx={{ ml: 2 }}>{labels[hover !== -1 ? hover : value]}</Box>
      )}
      </Box>
      <button
        id="send"
        className="feedback-thumbs-button"
      >
        <TbFileExport style={{ color: "#A7A4C4" }} size="20px" />
      </button>
    </div>
  );
}
