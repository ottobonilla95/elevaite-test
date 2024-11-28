import { CommonButton, CommonMenu, ElevaiteIcons, type CommonMenuItem } from "@repo/ui/components";
import { type ContractObject, type UnverifiedItem } from "src/interfaces";



interface MismatchButtonProps {
    contract: ContractObject;
    items: UnverifiedItem[];
    index?: number;
    listLength?: number;
    handleContractClick: (contractId: string | number, comparedContractId: string | number) => void;
}

export function MismatchButton(props: MismatchButtonProps): JSX.Element {
    if (props.items.length === 0) return (
        <span className="failed" title="This hasn't been matched with any files from this column">
            <ElevaiteIcons.SVGXmark />
        </span>
    );


    function handleMismatchMenuClick(clickedItem: UnverifiedItem): void {
        if (!clickedItem.id) return;
        props.handleContractClick(props.contract.id, clickedItem.id);
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
