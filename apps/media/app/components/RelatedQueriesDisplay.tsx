import React from 'react';
import { RelatedQueriesDisplayProps } from '../lib/interfaces';
import './RelatedQueriesDisplay.scss';
import  SVGMagnifyingGlass  from '../../../../packages/ui/src/components/icons/elevaite/svgMagnifyingGlass'



const RelatedQueriesDisplay: React.FC<RelatedQueriesDisplayProps> = ({ queries, onQueryClick }) => {
    console.log(queries);
    return (
        <div className="related-queries-container">
            <h4>Related:</h4>
            <ul>
                {queries.map((query, index) => (
                    <div key={index} onClick={() => onQueryClick(query)} className="query-item">
                        <span className="query-text">{query}</span>
                        <SVGMagnifyingGlass className="query-icon"/>
                    </div>
                ))}
            </ul>
        </div>
    );
};
export default RelatedQueriesDisplay;