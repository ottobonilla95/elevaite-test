import { CommonButton, CommonMenu, ElevaiteIcons, type CommonMenuItem } from "@repo/ui/components";
import { useContracts } from "../../../../lib/contexts/ContractsContext";
import { type ContractObject, type UnverifiedItem } from "../../../../lib/interfaces";



interface MismatchButtonProps {
    contract: ContractObject;
    items: UnverifiedItem[];
    index?: number;
    listLength?: number;
}

export function MismatchButton(props: MismatchButtonProps): JSX.Element {
    const contractsContext = useContracts();
    if (props.items.length === 0) return <span className="failed"><ElevaiteIcons.SVGXmark /></span>


    function handleMismatchMenuClick(clickedItem: UnverifiedItem): void {
        if (!clickedItem.id) return;
        contractsContext.setSecondarySelectedContractById(clickedItem.id);
        contractsContext.setSelectedContract(props.contract);
    }

    if (props.items.length === 1)
        return (
            <CommonButton
                title={`This cross-section has one issue, with file:\n${props.items[0].label ?? props.items[0].fileName ?? "Unknown File"}`}
                onClick={() => { handleMismatchMenuClick(props.items[0]); }}
            >
                <ElevaiteIcons.SVGQuestionMark />
            </CommonButton>
        );

    //--------------------

    const mismatchMenu: CommonMenuItem<UnverifiedItem[]>[] =
        props.items.map(item => {
            return {
                label: item.label ?? item.fileName ?? "Unknown File",
                onClick: () => { handleMismatchMenuClick(item); },
                tooltip: item.fileName,
            }}
        );

    return (
        <CommonMenu
            menu={mismatchMenu}
            menuIcon={<ElevaiteIcons.SVGQuestionMark />}
            tooltip={`This cross-section has ${props.items.length.toString()} issues`}
            labelWidth="long"
            left
            top={Boolean(props.listLength && props.index && props.listLength > 4 && props.index > (props.listLength - 4))}
        />
    );
}
