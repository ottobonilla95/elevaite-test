"use client";

import { useState } from "react";
import { CommonButton, ElevaiteIcons } from "@repo/ui/components";
import { ProjectSidebar } from "../components/advanced/ProjectSidebar";
import "./page.scss";

const LockIcon = ({ size = 14 }: { size?: number }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
  >
    <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
    <circle cx="12" cy="16" r="1" />
    <path d="M7 11V7a5 5 0 0 1 10 0v4" />
  </svg>
);

const KeyIcon = ({ size = 14 }: { size?: number }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
  >
    <circle cx="7" cy="7" r="3" />
    <path d="m10 10 11 11" />
    <path d="m15 15 1 1" />
    <path d="m18 18 1 1" />
  </svg>
);

export default function Settings(): JSX.Element {
  const [isExpanded, setIsExpanded] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState<string>("profile");
  const [selectedSubcategory, setSelectedSubcategory] = useState<string>("");

  const handleCategoryClick = (category: string) => {
    if (selectedCategory === category) {
      // If clicking the same category, toggle it closed
      setSelectedCategory("");
      setSelectedSubcategory("");
    } else {
      // If clicking a different category, open it
      setSelectedCategory(category);
      setSelectedSubcategory(""); // Reset subcategory when changing main category
    }
  };

  const handleSubcategoryClick = (subcategory: string) => {
    setSelectedSubcategory(subcategory);
  };

  const renderContent = () => {
    if (
      selectedCategory === "security" &&
      selectedSubcategory === "change-password"
    ) {
      return (
        <div className="settings-content-display">
          <h2>Change Password</h2>
          <p className="hint-text">
            Your new password must be at least 9 characters long and include
            uppercase letters, lowercase letters, numbers, and special
            characters.
          </p>
        </div>
      );
    }

    // Show nothing when no specific subcategory is selected
    return null;
  };

  return (
    <main
      className={`settings-advanced-container ${isExpanded ? "sidebar-expanded" : "sidebar-collapsed"}`}
    >
      <ProjectSidebar isExpanded={isExpanded} setIsExpanded={setIsExpanded} />
      <div className="settings-main-area">
        <div className="settings-header">
          <span>Settings</span>
        </div>
        <div className="settings-content">
          <div className="settings-layout">
            <div className="settings-left-column">
              <div className="category-navigation">
                {/* Profile Category */}
                <CommonButton
                  className={`category-button ${selectedCategory === "profile" ? "selected" : ""}`}
                  onClick={() => handleCategoryClick("profile")}
                  noBackground
                >
                  <span>Profile</span>
                  <ElevaiteIcons.SVGChevron className="accordion-arrow" />
                </CommonButton>

                {/* Account Category */}
                <CommonButton
                  className={`category-button ${selectedCategory === "account" ? "selected" : ""}`}
                  onClick={() => handleCategoryClick("account")}
                  noBackground
                >
                  <span>Account</span>
                  <ElevaiteIcons.SVGChevron className="accordion-arrow" />
                </CommonButton>

                {/* Security Category */}
                <CommonButton
                  className={`category-button ${selectedCategory === "security" ? "selected" : ""} ${selectedCategory === "security" ? "expanded" : ""}`}
                  onClick={() => handleCategoryClick("security")}
                  noBackground
                >
                  <span>Security</span>
                  <ElevaiteIcons.SVGChevron className="accordion-arrow" />
                </CommonButton>

                {/* Security Subcategories */}
                {selectedCategory === "security" && (
                  <div className="subcategory-list">
                    <CommonButton
                      className={`subcategory-button ${selectedSubcategory === "change-password" ? "selected" : ""}`}
                      onClick={() => handleSubcategoryClick("change-password")}
                      noBackground
                    >
                      <LockIcon size={14} />
                      <span>Change Password</span>
                    </CommonButton>
                    <CommonButton
                      className={`subcategory-button ${selectedSubcategory === "multi-factor-auth" ? "selected" : ""}`}
                      onClick={() =>
                        handleSubcategoryClick("multi-factor-auth")
                      }
                      noBackground
                    >
                      <KeyIcon size={14} />
                      <span>Multi-Factor Authentication</span>
                    </CommonButton>
                  </div>
                )}
              </div>
            </div>

            <div className="settings-right-column">{renderContent()}</div>
          </div>
        </div>
      </div>
    </main>
  );
}
