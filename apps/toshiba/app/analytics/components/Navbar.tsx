import React from "react";
import { FiDownload } from "react-icons/fi";
import "./Navbar.scss";

const Navbar = (): JSX.Element => {
    return (
        <div className="navbar">
            <div className="textContent">
                <h1>TGCS Service Request Analytics</h1>
                <p>Monitor and analyze service request performance</p>
            </div>
            {/* <button className="exportBtn">
                <FiDownload className="icon" />
                Export Data
            </button> */}
        </div>
    );
};

export { Navbar };
