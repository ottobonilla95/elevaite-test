import { CommonButton } from "@repo/ui/components";
import { type ExtractionStatus, type MatchingStatus } from "src/interfaces";
import "./ContractListStatusBlock.scss";
import { StatusIcon } from "./StatusIcon";






interface ContractListStatusBlockProps {
    amount: number;
    title: ExtractionStatus | MatchingStatus;
    selectedStatus: ExtractionStatus | MatchingStatus | undefined;
    onClick: (status: ExtractionStatus | MatchingStatus) => void;
}

export function ContractListStatusBlock(props: ContractListStatusBlockProps): JSX.Element {

    function handleClick(): void {
        props.onClick(props.title);
    }

    return (
        <CommonButton
            className={[
                "contract-list-status-block-container",
                props.title === props.selectedStatus ? "active" : undefined,
            ].filter(Boolean).join(" ")}
            onClick={handleClick}
            disabled={props.amount === 0}
        >
            <div className="amount">{props.amount.toString().padStart(2, "0")}</div>
            <StatusIcon status={props.title} />
            <div className="title">{props.title}</div>
        </CommonButton>
    );
}