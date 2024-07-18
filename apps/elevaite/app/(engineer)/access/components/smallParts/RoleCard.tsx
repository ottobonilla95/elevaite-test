import { CommonButton } from "@repo/ui/components";
import { type RoleObject } from "../../../../lib/interfaces";
import "./RoleCard.scss";



interface RoleCardProps {
    role: RoleObject;
    selectedRoleId?: string;
    handleClick: (role: RoleObject) => void;
}

export function RoleCard(props: RoleCardProps): JSX.Element {
    const test = "Test";
    const secondaryTest = "This is a very long sentence just to see what's going on and if it's behaving as it should.";

    function handleClick(): void {
        props.handleClick(props.role);
    }

    return (
        <CommonButton
            className={["role-card-container", props.role.id === props.selectedRoleId ? "selected" : undefined].filter(Boolean).join(" ")}
            onClick={handleClick}
            overrideClass
        >
            <div className="role-card-line">
                <span className="main">{props.role.name}</span>
                {!props.role.name ? undefined : // Fix this
                    <>
                    <span>|</span>
                    <span className="secondary cut-overflow" title={test}>{test}</span>
                    </>
                } 
            </div>
            <div className="role-card-line">
                <span>HR</span>
                {!props.role.name ? undefined : // Fix this
                    <>
                    <span>•</span>
                    <span className="cut-overflow" title={secondaryTest}>{secondaryTest}</span>
                    </>
                }
            </div>
        </CommonButton>
    );
}