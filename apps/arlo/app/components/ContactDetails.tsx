"use client";
import "./ContactDetails.scss";
import {ChatContext} from "../ui/contexts/ChatContext.tsx";
import {useContext, useEffect, useState} from "react";


const labels = {
    email: "Email:",
    phone: "Phone:",
    issue: "Issue:",
    product: "Product:",
}



export function ContactDetails(): JSX.Element {
    const chatContext = useContext(ChatContext);

    const [testData, setTestData] = useState({
        referenceNumber: "0000",
        name: "",
        product: "",
        issue: "",
        email: "",
        phone: "",
    });

    useEffect(() => {
        if (chatContext.selectedSession) {
            setTestData({
                referenceNumber: chatContext.selectedSession.caseID ?? "0000",
                name: chatContext.selectedSession.contactDetails?.customerName ?? "",
                product: chatContext.selectedSession.contactDetails?.productName ?? "",
                issue: chatContext.selectedSession.contactDetails?.issue ?? "",
                email: chatContext.selectedSession.contactDetails?.email ?? "",
                phone: chatContext.selectedSession.contactDetails?.phoneNumber ?? "",
            });
        }
    }, [chatContext.selectedSession]);
    // Set up the context link here, get reference to the selected case, and replace test-data with data from it.
    if (!chatContext.selectedSession) return <div>No info available</div>;
    // const testData = {
    //     referenceNumber: chatContext.selectedSession?.caseID ?? "0000",
    //     name: chatContext.selectedSession?.contactDetails?.customerName,
    //     product: chatContext.selectedSession?.contactDetails?.productName,
    //     issue: chatContext.selectedSession?.contactDetails?.issue,
    //     email: chatContext.selectedSession?.contactDetails?.email,
    //     phone: chatContext.selectedSession?.contactDetails?.phoneNumber,
    // };

    return (
        <div className="contact-details-container">
            <div className="reference">{testData.referenceNumber}</div>
            <div className="name-and-type-container">
                <span className="name">{testData.name}</span>
            </div>
            <div className="address-container">
                <div className="address-bit">
                    <span>{labels.issue}</span>
                    <span>{testData.issue}</span>
                </div>
                <div className="address-bit">
                    <span>{labels.product}</span>
                    <span>{testData.product}</span>
                </div>
                <div className="address-bit">
                    <span>{labels.email}</span>
                    <span>{testData.email}</span>
                </div>
                <div className="address-bit">
                    <span>{labels.phone}</span>
                    <span>{testData.phone}</span>
                </div>

            </div>
        </div>
    );
}