"use client";
import { useState } from "react";
import "./ContactDetails.scss";
import { ElevaiteIcons } from "@repo/ui/components";


const testData = {
    referenceNumber: "ACCT9183948",
    name: "Mark Johnson",
    type: "Residential",
    email: "mark.johnson123@example.com",
    phone: "+1-555-789-3456",
    address: "123 Main Street, Springfield, IL, USA"
};




const labels = {
    email: "Email:",
    phone: "Phone:",
    address: "Address:",
}



export function ContactDetails(): JSX.Element {
    const [details, setDetails] = useState(testData); // Get this from the context
    const [loading, setLoading] = useState(false); // Get this from the context
    

    return (
        <div className="contact-details-container">
            {loading ? 
                <div className="centered loading">
                    <ElevaiteIcons.SVGSpinner/>
                </div>
            : !details ? 
                <div className="centered empty-details">
                    <div>Please add the case information in the chat to view account details</div>
                </div>
            : <>
                <div className="reference">{testData.referenceNumber}</div>
                <div className="name-and-type-container">
                    <span className="name">{testData.name}</span>
                    <span className="type">{testData.type}</span>
                </div>
                <div className="address-container">
                    <div className="address-bit">
                        <span>{labels.email}</span>
                        <span>{testData.email}</span>
                    </div>
                    <div className="address-bit">
                        <span>{labels.phone}</span>
                        <span>{testData.phone}</span>
                    </div>
                    <div className="address-bit">
                        <span>{labels.address}</span>
                        <span>{testData.address}</span>
                    </div>
                </div>
            </>
            }
        </div>
    );
}