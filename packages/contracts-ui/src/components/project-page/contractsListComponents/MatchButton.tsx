import { CommonButton, ElevaiteIcons } from "@repo/ui/components";
import { type ContractObject, type ContractObjectVerificationItem } from "../../../../src/interfaces";





interface MatchButtonProps {
    contract: ContractObject;
    handleContractClick: (contractId: string | number, comparedContractId: string | number) => void;
}

export function MatchButton(props: MatchButtonProps): JSX.Element {
    
    function handleMatchClick(): void {
        if (!props.contract.verification) return;
        const relevantContracts = Object.values(props.contract.verification)
            .filter((value): value is ContractObjectVerificationItem[] => Array.isArray(value)).flat();

        const firstItem: ContractObjectVerificationItem = relevantContracts[0];

        if (firstItem?.file_id) {
            props.handleContractClick(props.contract.id, firstItem.file_id);
        }
    }


    return (
        <CommonButton
            className="verified"
            title="This cross-section has no issues"
            onClick={handleMatchClick}
        >
            <ElevaiteIcons.SVGCheckmark />
        </CommonButton>
    );
}
