import { CommonButton } from "@repo/ui/components";
import { useEffect, useState } from "react";
import { CONTRACT_TYPES, CONTRACTS_TABS } from "src/interfaces";
import "./ContractListFilterPill.scss";




interface ContractListFilterPillProps {
    type: CONTRACT_TYPES;
    selectedPills: CONTRACT_TYPES[];
    onClick: (selectedTab: CONTRACT_TYPES) => void;
}

export function ContractListFilterPill(props: ContractListFilterPillProps): JSX.Element {
    const [label, setLabel] = useState("");
    const [isSelected, setIsSelected] = useState(false);

    useEffect(() => {
        switch (props.type) {
            case CONTRACT_TYPES.VSOW: setLabel(CONTRACTS_TABS.SUPPLIER_CONTRACTS.toUpperCase()); break;
            case CONTRACT_TYPES.CSOW: setLabel(CONTRACTS_TABS.CUSTOMER_CONTRACTS.toUpperCase()); break;
            case CONTRACT_TYPES.PURCHASE_ORDER: setLabel(CONTRACTS_TABS.SUPPLIER_POS.toUpperCase()); break;
            case CONTRACT_TYPES.INVOICE: setLabel(CONTRACTS_TABS.SUPPLIER_INVOICES.toUpperCase()); break;
        }
    }, [props.type]);

    useEffect(() => {
        setIsSelected(props.selectedPills.includes(props.type));
    }, [props.type, props.selectedPills]);

    function handleClick(): void {
        props.onClick(props.type);
    }

    return (
        <CommonButton
            className={["filter-pill-container", isSelected ? "active" : undefined].filter(Boolean).join(" ")}
            onClick={handleClick}
            noBackground={!isSelected}
        >
            {label}
        </CommonButton>
    );
}

