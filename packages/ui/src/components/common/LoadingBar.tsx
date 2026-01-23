import type { JSX } from "react";
import "./LoadingBar.scss";



interface LoadingBarProps {

}

export function LoadingBar(props: LoadingBarProps): JSX.Element {
    return (
        <div className="loading-bar-container">
            <div className="loading-bar-content"/>
        </div>
    );
}