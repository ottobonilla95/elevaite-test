/* eslint-disable @next/next/no-img-element */
import { useEffect, useRef, useState } from "react";
import Backdrop from "@mui/material/Backdrop";
import Box from "@mui/material/Box";
import Modal from "@mui/material/Modal";
import Fade from "@mui/material/Fade";
import Button from "@mui/material/Button";
import Typography from "@mui/material/Typography";
import axios from "axios";
import FormControl from "@mui/joy/FormControl";
import FormLabel from "@mui/joy/FormLabel";
import FormHelperText from "@mui/joy/FormHelperText";
import Textarea from "@mui/joy/Textarea";
import CircularIndeterminate from "./progress_spinner";

const style = {
  position: "absolute" as "absolute",
  top: "50%",
  left: "50%",
  transform: "translate(-50%, -50%)",
  width: 900,
  height: 575,
  bgcolor: "#514f72",
  border: "2px solid #000",
  boxShadow: 24,
  borderRadius: 4,
  p: 4,
};

export default function TransitionsModal(props: any) {
  const [open, setOpen] = useState(false);
  const [title, setTitle] = useState("");
  const [problemDescription, setProblemDescription] = useState("");
  const [solutionDescription, setSolutionDescription] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const handleOpen = () => {
    setOpen(true);
    getSummaryDetails();
  };
  function handleSubmit() {
    setOpen(false);
    props.clearMessages();
  }
  function handleClose() {
    setOpen(() => false);
  }

  function getSummaryDetails() {
    setIsLoading(() => true);
    axios
      .get(
        process.env.NEXT_PUBLIC_BACKEND_URL +
          "summarization?uid=" +
          props.uid +
          "&sid=" +
          props?.sid.toString()
      )
      .then((res: any) => {
        setTitle(() => res.data.title);
        setProblemDescription(() => res.data.problem);
        setSolutionDescription(() => res.data.solution);
        setIsLoading(() => false);
      });
  }

  return (
    <div>
      {/* <button className="button session-button" onClick={handleOpen}>
        <img src="/img/session-button.svg" alt="session button" />
      </button> */}
      <button className="button session-button" onClick={handleOpen}>
        <img src="/img/Frame 2095584750.svg" alt="session button" />
      </button>
      <Modal
        aria-labelledby="transition-modal-title"
        aria-describedby="transition-modal-description"
        open={open}
        onClose={handleClose}
        closeAfterTransition
        slots={{ backdrop: Backdrop }}
        slotProps={{
          backdrop: {
            timeout: 500,
          },
        }}
      >
        <Fade in={open}>
          <Box sx={style}>
            {isLoading ? (
              <div className="summary-loading">
                <Box
                  sx={{
                    width: "100%",
                    display: "flex",
                    flexDirection: "column",
                    justifyContent: "center",
                    alignItems: "center",
                    color: "white",
                  }}
                >
                  <CircularIndeterminate size={60} />
                  Generating a summary of the incident
                </Box>
              </div>
            ) : (
              <>
                <div className="summary-modal">
                  <p style={{ textAlign: "left" }}> Case Summary</p>
                  <FormControl className="summary-element">
                    <FormLabel style={{ color: "white" }}>Title</FormLabel>
                    <Textarea
                      placeholder="Title"
                      className="summary-element-title"
                      minRows={1}
                      value={title}
                      onChange={(e) => setTitle(() => e.target.value)}
                    />
                  </FormControl>
                  <FormControl className="summary-element">
                    <FormLabel style={{ color: "white" }}>
                      Problem Description
                    </FormLabel>
                    <Textarea
                      placeholder="Problem Description"
                      className="summary-element-problem"
                      minRows={1}
                      value={problemDescription}
                      onChange={(e) =>
                        setProblemDescription(() => e.target.value)
                      }
                    />
                  </FormControl>
                  <FormControl className="summary-element">
                    <FormLabel style={{ color: "white" }}>Solution</FormLabel>
                    <Textarea
                      placeholder="Solution"
                      className="summary-element-solution"
                      minRows={5}
                      style={{ overflowY: "scroll" }}
                      value={solutionDescription}
                      onChange={(e) =>
                        setSolutionDescription(() => e.target.value)
                      }
                    />
                  </FormControl>
                  <div className="summary-modal-button-group">
                    <button
                      className="summary-modal-button cancel"
                      onClick={handleClose}
                    >
                      Cancel
                    </button>
                    <button
                      className="summary-modal-button"
                      onClick={handleSubmit}
                    >
                      Submit
                    </button>
                  </div>
                </div>
              </>
            )}
          </Box>
        </Fade>
      </Modal>
    </div>
  );
}
