import { CommonButton, ElevaiteIcons } from "@repo/ui/components";
import { useContracts } from "../../../../lib/contexts/ContractsContext";
import { type ContractObject, type ContractObjectVerificationItem } from "../../../../lib/interfaces";





interface MatchButtonProps {
    contract: ContractObject;
}

export function MatchButton(props: MatchButtonProps): JSX.Element {
    const contractsContext = useContracts();
    
    function handleMatchClick(): void {
        if (!props.contract.verification) return;
        const relevantContracts = Object.values(props.contract.verification)
            .filter((value): value is ContractObjectVerificationItem[] => Array.isArray(value)).flat();

        if (relevantContracts[0]) {            
            contractsContext.setSecondarySelectedContractById(relevantContracts[0].file_id);
            contractsContext.setSelectedContract(props.contract);
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
