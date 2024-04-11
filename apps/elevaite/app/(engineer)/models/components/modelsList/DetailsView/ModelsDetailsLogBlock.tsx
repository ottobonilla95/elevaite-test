"use client";
import { CommonButton, ElevaiteIcons, SimpleInput } from "@repo/ui/components";
import dayjs from "dayjs";
import { useEffect, useRef, useState } from "react";
import { type ModelLogObject } from "../../../../../lib/interfaces";
import "./ModelsDetailsLogBlock.scss";




interface ModelsDetailsLogBlockProps {
    id: string;
    logs: ModelLogObject[];
    date?: string;
    isHidden?: boolean;
    isOpen?: boolean;
    isLoading?: boolean;
    onToggleSize?: (id: string) => void;
}

export function ModelsDetailsLogBlock(props: ModelsDetailsLogBlockProps): JSX.Element {
    const searchRef = useRef<HTMLInputElement|null>(null);
    const [isSearchOpen, setIsSearchOpen] = useState(false);
    const [searchTerm, setSearchTerm] = useState("");


    useEffect(() => {
        if (!isSearchOpen) setSearchTerm("");
        else if (searchRef.current) {
            searchRef.current.focus();
        }
    }, [isSearchOpen]);

    useEffect(() => {
        if (props.isOpen) return;
        setSearchTerm("");
        setIsSearchOpen(false);
    }, [props.isOpen]);


    function toggleSearch(): void {
        setIsSearchOpen(current => !current);
    }

    function toggleSize(): void {
        if (!props.onToggleSize) return;
        props.onToggleSize(props.id);
    }



    return (
        <div className={[
            "models-details-log-block-container",
            props.isHidden ? "hidden" : undefined,
            props.isOpen && !props.isHidden ? "open" : "closed"
        ].filter(Boolean).join(" ")}>
            <div className="log-block-header">
                <span>{!props.date ? "Registration Log": `${dayjs(props.date).format("MMMM DD YYYY")} Evaluation`}</span>
                <div className={["search-container", isSearchOpen ? "open" : undefined].filter(Boolean).join(" ")}>
                    <div className="search-input-container">
                        <SimpleInput
                            passedRef={searchRef}
                            value={searchTerm}
                            onChange={setSearchTerm}
                            autoComplete="false"
                            autoCorrect="false"
                            spellCheck="false"
                            placeholder="Search the log"
                        />
                    </div>
                    <CommonButton
                        className="search-button"
                        onClick={toggleSearch}
                        noBackground
                    >
                        <ElevaiteIcons.SVGMagnifyingGlass/>
                    </CommonButton>
                    {!props.onToggleSize ? null :
                        <CommonButton
                            onClick={toggleSize}
                            noBackground
                        >
                            <ElevaiteIcons.SVGToggleSize/>
                        </CommonButton>
                    }
                </div>
            </div>

            <div className={["log-block-wrapper", props.isOpen && !props.isHidden ? "open" : undefined].filter(Boolean).join(" ")}>

                <div className="log-block-accordion">
                    <div className="log-block-contents">

                        {props.isLoading ? 
                            <div className="loading">
                                <ElevaiteIcons.SVGSpinner/>
                                <span>Loading...</span>
                            </div>
                            : props.logs.length === 0 ? 
                            <div className="empty-log">There are no logs for this model.</div>
                            :
                            props.logs.map(log => {
                                if (!log.message.trim()) return undefined;
                                return <ModelLogBit key={log.id} log={log} searchTerm={searchTerm} />
                            })
                        }
                        
                    </div>
                </div>
            </div>

                
        </div>
    );
}





interface ModelLogBitProps {
    log: ModelLogObject;
    searchTerm?: string;
}

function ModelLogBit({log, searchTerm}: ModelLogBitProps): JSX.Element {
    const [message, setMessage] = useState<React.ReactNode>(<span>{log.message}</span>);
    const [isHighlighted, setIsHighlighted] = useState(false);

    useEffect(() => {
        if (searchTerm && log.message.includes(searchTerm)) {
            const highlight = log.message.split(searchTerm);
            if (highlight.length === 2) {
                setMessage(
                    <span>
                        {highlight[0]}
                        <span className="highlight">
                            {searchTerm}
                        </span>
                        {highlight[1]}
                    </span>
                );
                setIsHighlighted(true);
            } else refresh();
        } else refresh();
    }, [log.message, searchTerm]);

    function refresh(): void {
        setMessage(<span>{log.message}</span>);
        setIsHighlighted(false);
    }


    return (
        <div className={["model-log-bit-container", isHighlighted ? "highlight" : undefined].filter(Boolean).join(" ")}>
            <span className="entry-label">{dayjs(log.time).format("YYYY-MM-DD HH:mm:ss")}</span>
            <span>{message}</span>
        </div>
    );
}

