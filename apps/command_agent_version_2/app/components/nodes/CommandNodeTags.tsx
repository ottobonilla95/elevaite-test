import { type CommandNodeTagProps } from "../../lib/interfaces";
import "./CommandNodeTags.scss";

import type { JSX } from "react";

const SHOW_ALL_TAGS_ON_OVERFLOW = true;


export function CommandNodeTag(props: CommandNodeTagProps): JSX.Element {
    return (
        <div
            className="command-node-tag"
            style={{
                color: props.color,
                backgroundColor: props.background,
            }}
        >
            {props.icon}
            <span>{props.label}</span>
        </div>
    );
}




interface CommandNodeTagsProps {
    tags: CommandNodeTagProps[];
}

export function CommandNodeTags({tags}: CommandNodeTagsProps): JSX.Element {
    const bottomRowTags = tags.slice(0, 4);
    const hasOverflow = tags.length > 8;
    const topRowTags = tags.slice(4, hasOverflow ? 7 : 8);
    const overflowTags = tags.slice(7);
    
    // eslint-disable-next-line @typescript-eslint/no-unnecessary-condition -- Feature flag for configuration
    const popoverTags = SHOW_ALL_TAGS_ON_OVERFLOW ? tags : overflowTags;    
    const topRowCount = topRowTags.length + (hasOverflow ? 1 : 0);
    const bottomRowCount = bottomRowTags.length;

    return (
        <div className="command-node-tags-container" data-row-count={tags.length > 4 ? 2 : 1}>
            {tags.length > 4 && (
                <div className="command-node-tags-row top-row" data-item-count={topRowCount}>
                    {topRowTags.map((tag, index) => 
                        <CommandNodeTag key={`${tag.label}-${(4 + index).toString()}`} {...tag}/>
                    )}
                    {!hasOverflow ? undefined :
                        <div className="command-node-tag overflow-tag nodrag nopan"
                            onWheelCapture={(event) => { event.stopPropagation(); } }
                        >
                            +{overflowTags.length}
                            
                            <div className="overflow-popover">
                                {popoverTags.map((tag, index) => (
                                    <CommandNodeTag key={`popover-${tag.label}-${index.toString()}`} {...tag}/>
                                ))}
                            </div>
                        </div>
                    }
                </div>
            )}
            <div 
                className="command-node-tags-row"
                data-item-count={bottomRowCount}
            >
                {bottomRowTags.map((tag, index) => 
                    <CommandNodeTag key={`${tag.label}-${index.toString()}`} {...tag}/>
                )}
            </div>
        </div>
    );
}