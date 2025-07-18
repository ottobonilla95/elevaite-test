import "./ChatLoading.scss";

interface ChatLoadingProps {
	isLoading?: boolean;
	loadingMessage?: string;
    className?: string;
}

export function ChatLoading({ isLoading, loadingMessage }: ChatLoadingProps): React.ReactNode {

	return (
		<div className={["chat-loading-container"].filter(Boolean).join(" ")}>
            {isLoading === false ? undefined :
                <>
                    <div className="chat-loading-text">
                        <div className="dot-pulse-loader">
                            <span />
                            <span />
                            <span />
                        </div>
                        {loadingMessage}
                    </div>
                    <div className="chat-loading-line" />
                </>
            }
		</div>
	);
}