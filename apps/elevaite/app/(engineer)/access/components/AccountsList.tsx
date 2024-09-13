"use client";
import { CommonModal, ElevaiteIcons, type CommonMenuItem } from "@repo/ui/components";
import { useEffect, useState } from "react";
import { ListHeader } from "../../../lib/components/ListHeader";
import { ListRow, specialHandlingListRowFields, type RowStructure } from "../../../lib/components/ListRow";
import { useRoles } from "../../../lib/contexts/RolesContext";
import { type AccountObject, type ExtendedAccountObject, type SortingObject } from "../../../lib/interfaces";
import "./AccountsList.scss";
import { AddEditAccount } from "./Add Edit Modals/AddEditAccount";




enum menuActions {
    EDIT = "Edit",
};




interface AccountsListProps {
    isVisible: boolean;
}

export function AccountsList(props: AccountsListProps): JSX.Element {
    const rolesContext = useRoles();
    const [displayAccounts, setDisplayAccounts] = useState<ExtendedAccountObject[]>([]);
    const [searchTerm, setSearchTerm] = useState("");
    const [sorting, setSorting] = useState<SortingObject<ExtendedAccountObject>>({field: undefined});
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [selectedAccount, setSelectedAccount] = useState<ExtendedAccountObject|undefined>();

    
    const accountsListStructure: RowStructure<ExtendedAccountObject>[] = [
        { header: "Account Name", field: "name", isSortable: true },
        { header: "Description", field: "description", isSortable: false },
        { header: "Projects", field: "projectCount", isSortable: true, align: "right", specialHandling: specialHandlingListRowFields.COUNT },
    ];

    const accountsListMenu: CommonMenuItem<ExtendedAccountObject>[] = [
        { label: "Edit Account", onClick: (item: ExtendedAccountObject) => { handleMenuClick(item, menuActions.EDIT); } },
    ];



    useEffect(() => {
        arrangeDisplayAccounts();
    }, [rolesContext.accounts, rolesContext.projects, searchTerm, sorting]);




    function arrangeDisplayAccounts(): void {
        const expandedAccounts = getAccountsWithAccountDetails(rolesContext.accounts ?? []);

        // Search
        const searchedList: ExtendedAccountObject[] = searchTerm ? [] : expandedAccounts;
        if (searchTerm) {
            for (const item of expandedAccounts) {
                if (item.name.toLowerCase().includes(searchTerm.toLowerCase())) { searchedList.push(item); continue; }
                if (item.description?.toLowerCase().includes(searchTerm.toLowerCase())) { searchedList.push(item); continue; }
                // Add other checks here as desired.                
            }
        }

        // Sort
        const sortedList: ExtendedAccountObject[] = searchedList;
        if (sorting.field) {
            sortedList.sort((a,b) => {
                if (sorting.field && typeof a[sorting.field] === "string" && typeof b[sorting.field] === "string" && !Array.isArray(a[sorting.field]) && !Array.isArray(b[sorting.field]))
                return (a[sorting.field] as string).localeCompare(b[sorting.field] as string);
                return 0;
            });
            if (sorting.isDesc) { sortedList.reverse(); }
        }

        // Set
        setDisplayAccounts(sortedList);
    }




    function handleAddAccount(): void {
        setIsModalOpen(true);
    }

    function handleEditAccount(account: ExtendedAccountObject): void {
        setSelectedAccount(account);
        setIsModalOpen(true);
    }

    function handleModalClose(): void {
        setSelectedAccount(undefined);
        setIsModalOpen(false);
    }

    function handleSearch(term: string): void {
        if (!props.isVisible) return;
        setSearchTerm(term);
    }

    function handleSort(field: keyof ExtendedAccountObject): void {
        let sortingResult: SortingObject<ExtendedAccountObject> = {};
        if (sorting.field !== field) sortingResult = {field};
        if (sorting.field === field) {
            if (sorting.isDesc) sortingResult = {field: undefined};
            else sortingResult = {field, isDesc: true};
        }
        setSorting(sortingResult);      
    }

    function handleMenuClick(account: ExtendedAccountObject, action: menuActions): void {
        switch (action) {
            case menuActions.EDIT: handleEditAccount(account); break;
            default: break;
        }
    }



    function getAccountsWithAccountDetails(accounts: AccountObject[]): ExtendedAccountObject[] {
        // Count projects per account
        const formattedAccounts = (JSON.parse(JSON.stringify(accounts)) as ExtendedAccountObject[]).map(account => {
            const projectCount = rolesContext.projects.filter(project => project.account_id === account.id).length;
            return {
                ...account,
                projectCount
            };
        });
        return formattedAccounts;
    }



    return (
        <div className="accounts-list-container">
            
            <ListHeader
                label="Accounts List"
                addLabel="Add Account"
                addIcon={<ElevaiteIcons.SVGAccounts/>}
                addAction={handleAddAccount}
                onSearch={handleSearch}
                searchPlaceholder="Search Accounts"
                isVisible={props.isVisible}
            />


            <div className="accounts-list-table-container">
                <ListRow<ExtendedAccountObject>
                    isHeader
                    structure={accountsListStructure}
                    menu={accountsListMenu}
                    onSort={handleSort}
                    sorting={sorting}
                />

                {displayAccounts.length === 0 && rolesContext.loading.accounts ?
                    <div className="table-span empty">
                        <ElevaiteIcons.SVGSpinner/>
                        <span>Loading...</span>
                    </div>
                    : displayAccounts.length === 0 ? 
                    <div className="table-span empty">
                        There are no accounts to display.
                    </div>

                :

                displayAccounts.map((account, index) => 
                    <ListRow<ExtendedAccountObject>
                        key={account.id}
                        rowItem={account}
                        structure={accountsListStructure}
                        menu={accountsListMenu}
                        menuToTop={displayAccounts.length > 4 && index > (displayAccounts.length - 4) }
                    />
                )}
            </div>


            {!isModalOpen ? null :
                <CommonModal onClose={handleModalClose}>
                    <AddEditAccount
                        account={selectedAccount}
                        onClose={handleModalClose}
                    />
                </CommonModal>
            }


        </div>
    );
}