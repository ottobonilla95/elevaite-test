import { CommonDialog } from "@repo/ui";
import "./ConfirmationPopup.scss";



import type { JSX } from "react";



interface ConfirmationPopupProps {
    title: string;
    onConfirm: () => void;
    onCancel?: () => void;
    confirmLabel?: string;
    cancelLabel?: string;
}

export function ConfirmationPopup(props: ConfirmationPopupProps): JSX.Element {
    return (
        <CommonDialog
            innerClassName="command-agent-confirmation-dialog"
            {...props}
        />
    );
}