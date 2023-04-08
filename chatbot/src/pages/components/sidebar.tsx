import React, { useState } from "react";
import { AiOutlinePlus } from "react-icons/ai";
export default function SideBar() {
  return (
    <>
      <div className="sidebar-container">
        <button className="sidebar-button">
          <AiOutlinePlus/>
          New Case
        </button>
      </div>
    </>
  );
}
