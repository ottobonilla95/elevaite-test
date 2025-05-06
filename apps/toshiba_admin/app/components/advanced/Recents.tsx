import { CommonButton, ElevaiteIcons } from "@repo/ui/components";
import dayjs from "dayjs";
import isBetween from "dayjs/plugin/isBetween";
import Image from "next/image";
import { useEffect, useState } from "react";
import "./Recents.scss";

// eslint-disable-next-line import/no-named-as-default-member -- I'm sure I didn't mean the other extend... >.<
dayjs.extend(isBetween);

// This should be modified and moved to the interfaces file.
interface RecentsItem {
    id: string;
    caseNumber: string;
    description: string;
    date: string;
}


// This should NOT be moved to interfaces, since it will only be used for front-end presentation on this page.
interface RecentsItemsList {
    label: string;
    items: RecentsItem[];
}

const testData: RecentsItem[] = [
    {
        id: "case00001",
        caseNumber: "CASE200091",
        description: "This is a description",
        date: dayjs().subtract(3, "days").toISOString(),
    },
    {
        id: "case00002",
        caseNumber: "CASE204535",
        description: "This is another description",
        date: dayjs().subtract(7, "months").toISOString(),
    },
    {
        id: "case00003",
        caseNumber: "CASE2654491",
        description: "This is a third, a little larger description just to see how things flow",
        date: dayjs().subtract(9, "months").toISOString(),
    },
    {
        id: "case00000",
        caseNumber: "CASE00000000",
        description: "The elder one",
        date: dayjs().subtract(12, "years").toISOString(),
    },
];

enum Labels {
    title = "Case Log",
    emptyGroup = "There are no cases in this timeframe.",
    groupsRecent = "Recent",
    groupsSixMonthsAgo = "6 months ago",
    groupsTwoYearsAgo = "Last two years",
    groupsOldest = "Older than two years",
}


export function Recents(): JSX.Element {
    const [displayRecents, setDisplayRecents] = useState<RecentsItemsList[]>();
    const [loading, setLoading] = useState(false); // Get this from the context


    useEffect(() => {
        setDisplayRecents(getDisplayRecents(testData));
    }, []); // Change the dependency array here to whatever variable you're getting from the context



    function handleCaseClick(id: string): void {
        console.log("Case clicked:", id, testData.find(item => item.id === id));
        // Open the selected case in the tabs.
    }




    // Get the array of items and make them into an object that we can iterate on the return function
    // It will include separators with labels (and possible menu actions)
    function getDisplayRecents(items: RecentsItem[], hideEmptyCategories = true): RecentsItemsList[] {
        const now = dayjs();

        // Define time boundaries
        const sixMonthsAgo = now.subtract(6, "months");
        const twoYearsAgo = now.subtract(2, "years");
    
        // Group items into categories
        const categories = {
            recent: items.filter(item => dayjs(item.date).isAfter(sixMonthsAgo)),
            sixMonthsAgo: items.filter(item => dayjs(item.date).isBetween(twoYearsAgo, sixMonthsAgo, null, "[)")),
            lastTwoYears: items.filter(item => dayjs(item.date).isBetween(twoYearsAgo.subtract(2, "years"), twoYearsAgo, null, "[)")),
            older: items.filter(item => dayjs(item.date).isBefore(twoYearsAgo))
        };
    
        // Build the result, sorting each category by date descending
        const result: RecentsItemsList[] = [
            { label: Labels.groupsRecent, items: categories.recent },
            { label: Labels.groupsSixMonthsAgo, items: categories.sixMonthsAgo },
            { label: Labels.groupsTwoYearsAgo, items: categories.lastTwoYears },
            { label: Labels.groupsOldest, items: categories.older }
        ]
            .map(category => ({
                ...category,
                items: category.items.sort((a, b) => dayjs(b.date).diff(dayjs(a.date)))
            }))
            .filter(category => !hideEmptyCategories || category.items.length > 0);
    
        return result;
    }



    return (
        <div className="recents-container">
            <div className="recents-header-container">
                <span>{Labels.title}</span>
            </div>
            {loading ? 
                <div className="centered loading">
                    <ElevaiteIcons.SVGSpinner/>
                </div>
            : !displayRecents ? 
                <div className="centered empty-details">
                    <Image src="/icons/empty-log-icon.png" alt="Empty Log Icon" width={250} height={200} />
                    <div>Please add the case information in the chat to view interaction logs</div>
                </div>
            :
                <div className="recents-scroller">
                    <div className="recents-contents">
                        {displayRecents.map(recentGroup => 
                            <div className="recents-group-container" key={recentGroup.label}>
                                <div className="group-header">
                                    {recentGroup.label}
                                </div>
                                <div className="group-contents">
                                    {recentGroup.items.length === 0 ? 
                                        <div className="empty-group">{Labels.emptyGroup}</div>
                                    :
                                        recentGroup.items.map(item => 
                                            <RecentsCard
                                                key={item.id}
                                                onClick={handleCaseClick}
                                                {...item}
                                            />
                                        )                                        
                                    }
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            }
        </div>
    );
}





type RecentsCardProps = RecentsItem & {
    onClick: (id: string) => void;
}

function RecentsCard(props: RecentsCardProps): JSX.Element {

    function handleClick(): void {
        props.onClick(props.id);
    }

    return (
        <div className="recents-card-container">
            <CommonButton
                className="recents-card-button"
                onClick={handleClick}
            >
                {props.caseNumber}
            </CommonButton>
            <span>{props.description}</span>
        </div>
    );
}