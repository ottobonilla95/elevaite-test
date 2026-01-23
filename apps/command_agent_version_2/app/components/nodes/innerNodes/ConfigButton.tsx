import { CommonButton, type CommonButtonProps } from "@repo/ui";
import { useConfigPanel } from "../../../lib/contexts/ConfigPanelContext";




import type { JSX } from "react";




interface ConfigButtonProps extends CommonButtonProps {
    anchor?: string;
}


export function ConfigButton({children, anchor, ...props}: ConfigButtonProps): JSX.Element {    
    const configPanel = useConfigPanel();

    function handleClick(): void {
        configPanel.openConfigPanel(anchor);
    }

    return (
        <CommonButton
            {...props}
            onClick={handleClick}
            className="config-button nopan nodrag"
        >
            {children}
        </CommonButton>
    );
}