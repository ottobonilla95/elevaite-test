import { ElevaiteIcons } from "../icons/elevaite";
import "./CommonFormLabels.scss";



interface CommonFormLabelsProps {
    label: string;
    info?: string;
    required?: boolean;
    errorMessage?: string;
    rightSideItem?: React.ReactNode;
    className?: string;
    children?: React.ReactNode;
}

export function CommonFormLabels(props: CommonFormLabelsProps): JSX.Element {
    return (
        <div className={[
            "common-form-labels-container",
            props.className,
        ].filter(Boolean).join(" ")}>
            <div className="labels">
                <span className="title">
                    {props.label}
                    { !props.required ? null : 
                        <span className={["required", props.errorMessage ? "unfulfilled" : undefined].filter(Boolean).join(" ")}>*</span>
                    }
                </span>
                {!props.info ? null :
                    <div className="info" title={props.info}><ElevaiteIcons.SVGInfo/></div>
                }
                <div className="error-message">{props.errorMessage ? props.errorMessage : undefined}</div>
                {props.rightSideItem ? props.rightSideItem : undefined}
            </div>
            {props.children}
        </div>
    );
}