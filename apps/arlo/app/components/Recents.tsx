"use client";
import dayjs from "dayjs";
import { useEffect, useContext, useState } from "react";
import "./Recents.scss";
import isBetween from "dayjs/plugin/isBetween";
import { CommonButton, ElevaiteIcons } from "@repo/ui/components";
import {ChatContext} from "../ui/contexts/ChatContext.tsx";

// eslint-disable-next-line import/no-named-as-default-member -- I'm sure I didn't mean the other extend... >.<
dayjs.extend(isBetween);

// This should be modified and moved to the interfaces file.
interface RecentsItem {
    id: string;
    caseId: string;
    subject: string;
    issue: string;
    symptom: string;
    problem: string;
    root_cause: string;
    product: string;
    date: string;
}


// This should NOT be moved to interfaces, since it will only be used for front-end presentation on this page.
interface RecentsItemsList {
    label: string;
    items: RecentsItem[];
}



const labels = {
    title: "Case Log",
    emptyGroup: "There are no cases in this timeframe.",
    groupsRecent: "Recent",
    groupsSixMonthsAgo: "6 months ago",
    groupsTwoYearsAgo: "Last two years",
    groupsOldest: "Older than two years",
}


export function Recents(): JSX.Element {
    const chatContext = useContext(ChatContext);
    // Set up the context link here, get reference to the selected case, and replace test-data with data from it.
    // You should keep a state of the whole array without mutations so that you can quickly and safel
    //y get information you need.
//     const testData: RecentsItem[] = chatContext.selectedSession?.opexData?.map((data, index) => ({
//     id: `case${String(index).padStart(5, '0')}`,
//     caseId: data.caseId ?? "Unknown",
//     subject: data.issue ?? "Unknown",
//     issue: data.symptom ?? "Unknown",
//     date: dayjs().subtract(index, "days").toISOString(),
//     symptom: data.symptom ?? "Unknown",
//     problem: data.problem ?? "Unknown",
//     root_cause: data.root_cause ?? "Unknown",
//     product: data.product ?? "Unknown",
// })) ?? [];


    const [testData, setTestData] = useState<RecentsItem[]>([]);

useEffect(() => {
    console.log("selectedSession changed in Recents:", chatContext.selectedSession);
    if (chatContext.selectedSession?.opexData) {
        const data = chatContext.selectedSession?.opexData.map((data, index) => ({
            id: `case${String(index).padStart(5, '0')}`,
            caseId: data.caseId ?? "Unknown",
            subject: data.issue ?? "Unknown",
            issue: data.symptom ?? "Unknown",
            date: dayjs().subtract(index, "days").toISOString(),
            symptom: data.symptom ?? "Unknown",
            problem: data.problem ?? "Unknown",
            root_cause: data.root_cause ?? "Unknown",
            product: data.product ?? "Unknown",
        }));
        setTestData(data);
    }
}, [chatContext.selectedSession]);
//
// if (!chatContext.selectedSession) return <div>No info available</div>;

    // const testData: RecentsItem[] = [
    //     {
    //         id: "case00001",
    //         caseId: chatContext.selectedSession?.opexData[0]?.caseId ?? "Unknown",
    //         subject: chatContext.selectedSession?.opexData[0]?.issue ?? "Unknown",
    //         issue: chatContext.selectedSession?.opexData[0]?.symptom ?? "Unknown",
    //         date: dayjs().subtract(3, "days").toISOString(),
    //         symptom: chatContext.selectedSession?.opexData[0]?.symptom ?? "Unknown",
    //         problem: chatContext.selectedSession?.opexData[0]?.problem ?? "Unknown",
    //         root_cause: chatContext.selectedSession?.opexData[0]?.root_cause ?? "Unknown",
    //         product: chatContext.selectedSession?.opexData[0]?.product ?? "Unknown",
    //     },
    //
    //     // {
    //     //     id: "case00002",
    //     //     caseNumber: chatContext.selectedSession?.opexData[0]?.caseId ?? "Unknown",
    //     //     description: chatContext.selectedSession?.opexData[0]?.issue ?? "Unknown",
    //     //     issue: chatContext.selectedSession?.opexData[0]?.symptom ?? "Unknown",
    //     //     date: dayjs().subtract(3, "days").toISOString(),
    //     // },
    //     // {
    //     //     id: "case00002",
    //     //     caseNumber: "CASE204535",
    //     //     description: "This is another description",
    //     //     date: dayjs().subtract(7, "months").toISOString(),
    //     // },
    //     // {
    //     //     id: "case00003",
    //     //     caseNumber: "CASE2654491",
    //     //     description: "This is a third, a little larger description just to see how things flow",
    //     //     date: dayjs().subtract(9, "months").toISOString(),
    //     // },
    //     // {
    //     //     id: "case00000",
    //     //     caseNumber: "CASE00000000",
    //     //     description: "The elder one",
    //     //     date: dayjs().subtract(12, "years").toISOString(),
    //     // },
    // ];

    const [displayRecents, setDisplayRecents] = useState<RecentsItemsList[]>();


    useEffect(() => {
        setDisplayRecents(getDisplayRecents(testData));
    }, [testData]); // Change the dependency array here to whatever variable you're getting from the context



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
            { label: labels.groupsRecent, items: categories.recent },
            { label: labels.groupsSixMonthsAgo, items: categories.sixMonthsAgo },
            { label: labels.groupsTwoYearsAgo, items: categories.lastTwoYears },
            { label: labels.groupsOldest, items: categories.older }
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
                <span>{labels.title}</span>
            </div>
            <div className="recents-scroller">
                <div className="recents-contents">
                    {!displayRecents ? <ElevaiteIcons.SVGSpinner/> :
                        displayRecents.map(recentGroup => 
                            <div className="recents-group-container" key={recentGroup.label}>
                                <div className="group-header">
                                    {recentGroup.label}
                                </div>
                                <div className="group-contents">
                                    {recentGroup.items.length === 0 ? 
                                        <div className="empty-group">{labels.emptyGroup}</div>
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
                        )
                    }
                </div>
            </div>
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
                {props.caseId}
            </CommonButton>
            {/*<span>{props.product!=="None" ?  props.product: null}</span>*/}
            {/*<span>{props.symptom!=="None" ? props.symptom: null}</span>*/}
            {/*<span>{props.root_cause!=="None"?props.root_cause:null}</span>*/}
            {Object.entries(props).map(([key, value]) => {
            if (key !== "caseId" && value !== "None" && key!=="onClick") {
                return (
                    <span key={key}>{key}: {value}</span>
                );
            }
            return null;
        })}

        </div>
    );
}