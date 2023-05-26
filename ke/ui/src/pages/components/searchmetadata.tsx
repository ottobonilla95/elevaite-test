import { TextareaAutosize } from "@mui/material";

type MessageProps = {
  change: any,
  ask: string,
  // handleKeyDown: any,
  placeHolder: string,
  readonly: boolean,
  classId:number
};
export default function SearchMetadata(props: MessageProps) {
  return (
    <div > <p className={"labelname"}> {props.placeHolder}: </p>
      <div className={"container-body-main container-body"+props.classId} >  
        <TextareaAutosize
            className="chat-input2"
            onChange={props.change}
            value={props.ask}
            // onKeyDown={props.handleKeyDown}
            placeholder={props.placeHolder}
            // readOnly={props.readonly}
            disabled={props.readonly}
          />
      </div>
    </div>
  );
}