"use client";
import { CommonButton, ElevaiteIcons, SimpleInput } from "@repo/ui/components";
import { useEffect, useRef, useState } from "react";
import "./ListHeader.scss";


const SEARCH_DEBOUNCE_TIME = 500; // milliseconds


interface ListHeaderProps {
    isVisible?: boolean;
    label: string | React.ReactNode;
    addLabel?: string;
    addIcon?: React.ReactNode;
    addAction?: () => void;
    onSearch: (term: string) => void;
    absoluteSearchPositioning?: boolean;
    searchPlaceholder?: string;
    debounce?: number;
}

export function ListHeader(props: ListHeaderProps): JSX.Element {
    const searchRef = useRef<HTMLInputElement|null>(null);
    const [isSearchOpen, setIsSearchOpen] = useState(false);
    const [searchTerm, setSearchTerm] = useState("");

    
    useEffect(() => {
        const debounceTimeout = setTimeout(() => {
            props.onSearch(searchTerm);
        }, props.debounce ?? SEARCH_DEBOUNCE_TIME);
        return () => { clearTimeout(debounceTimeout); };
    }, [searchTerm]);

    useEffect(() => {
        if (!isSearchOpen) setSearchTerm("");
        else if (searchRef.current) {
            searchRef.current.focus();
        }
    }, [isSearchOpen]);

    useEffect(() => {
        if (props.isVisible) return;
        setIsSearchOpen(false);
    }, [props.isVisible]);


    function toggleSearch(): void {
        setIsSearchOpen(current => !current);
    }

    
    return (
        <div className="list-header-container">
            <div className="header-label">
                    {props.label}
                </div>
                <div className="header-controls">

                    <div className={[
                        "search-container",
                        props.absoluteSearchPositioning ? "absolute-search" : undefined,
                        isSearchOpen ? "open" : undefined
                    ].filter(Boolean).join(" ")}>
                        <div className="search-input-container">
                            <SimpleInput
                                passedRef={searchRef}
                                value={searchTerm}
                                onChange={setSearchTerm}
                                autoComplete="false"
                                autoCorrect="false"
                                spellCheck="false"
                                placeholder={props.searchPlaceholder ?? "Search the list"}
                            />
                        </div>
                        <CommonButton
                            className="search-button"
                            onClick={toggleSearch}
                            noBackground
                        >
                            <ElevaiteIcons.SVGMagnifyingGlass/>
                        </CommonButton>
                    </div>

                    {!props.addAction ? undefined :
                        <CommonButton
                            className="add-button"
                            onClick={props.addAction}
                        >
                            {props.addIcon}
                            {props.addLabel}
                        </CommonButton>
                    }
                </div>
        </div>
    );
}