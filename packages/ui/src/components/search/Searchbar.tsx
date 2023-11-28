import "./Searchbar.css";

function Searchbar() {
  return (
    <div className="searchbarContainer">
      <div className="searchbar">
        <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
          <g opacity="0.5">
            <path
              d="M17.5 17.5L13.875 13.875M15.8333 9.16667C15.8333 12.8486 12.8486 15.8333 9.16667 15.8333C5.48477 15.8333 2.5 12.8486 2.5 9.16667C2.5 5.48477 5.48477 2.5 9.16667 2.5C12.8486 2.5 15.8333 5.48477 15.8333 9.16667Z"
              stroke="white"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </g>
        </svg>
        <input placeholder="Find answers" />
        {/* <label className="searchHotKeyHint">
          {navigator.platform.toUpperCase().indexOf("MAC") >= 0 ? "⌘" : "Ctrl"}+F
        </label> */}
      </div>
      {/* <div className="searchResults"></div> */}
    </div>
  );
}

export default Searchbar;
