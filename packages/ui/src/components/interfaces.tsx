

export interface SidebarIconObject {
    link: string;
    icon: React.ReactNode;
    description?: string;
}

export interface CommonSelectOption {
    label?: string;
    value: string;
    selectedLabel?: string; // Use this instead of label when it is the selected item
    icon?: React.ReactElement;
    disabled?: boolean;
    isSeparator?: React.ReactElement | boolean;
    suffix?: React.ReactNode;
    tooltip?: string | React.ReactNode;
    extras?: {
        prefix?: { label: string, tooltip?: string };
        postfix?: { label: string, tooltip?: string };
        footer?: { label: string, tooltip?: string }[];
    };
}
