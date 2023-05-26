import { TextField } from "@mui/material";
import Image from "next/image";
import plus from "../../../public/plus.png";
import bin from "../../../public/bin.png";
import edit from "../../../public/edit.png";


type MessageProps = {
  change: any,
  ask: string,
  // handleKeyDown: any,
  placeHolder: string,
  minRows: number,
  maxRows: number,
  readonly: boolean,
  label: string,
  classId: number,
  rteEdit: any,
  rteAdd : any,
  rteDel : any,
  visiblethreebtn : boolean
};

// Generic class for TextArea

export default function SearchTextArea(props: MessageProps) {
  // TODO: show the edit popup on mouse hover
  // TODO: add functionalities for plus and bin icons
  return (
    <div className={"section"+props.classId}>
      {props.visiblethreebtn?<div className={"showme labelCls hover:visible"}>
        <div className="moveBtn13"><Image alt="plus" className="" width={28} height={28} src={plus} onClick={props.rteAdd} ></Image></div>
        <div className="moveBtn14"><Image alt="edit" className="" width={14} height={14} src={edit} onClick={props.rteEdit}></Image></div>
        <div className="moveBtn15"><Image alt="bin" className="" width={14} height={14} src={bin} onClick={props.rteDel}></Image></div>
      </div>:""}
      <TextField
          minRows={props.minRows}
          maxRows={props.maxRows}
          className="chat-input"
          onChange={props.change}
          value={props.ask}
          placeholder={props.placeHolder}
          disabled={props.readonly}
          label={props.label}
          multiline={true}
          InputLabelProps={{
            style: {
              backgroundColor: '#A7A4C4',
              color: '#FFFFFF',
              borderRadius: '10px',
              height: '30px',
              padding: '3px',
            },
          }}
          sx={{
            '& textarea': {
              fontWeight: 'bold',
            },
          }}
        />
      </div>
  );
}