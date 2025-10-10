import { CommonButton, ElevaiteIcons, Logos } from "@repo/ui";
import { useEffect, useMemo, useState } from "react";
import "./ChatMessageVideoElement.scss";
import { ChatMessageVideoElementModal } from "./ChatMessageVideoElementModal";






export function normalizeYouTubeUrl(url: string, options?: {
        start?: number;
        end?: number;
        hideControls?: boolean;
        autoplay?: boolean;
        directLink?: boolean;
    }): string {
    try {
        const { start, end, hideControls, autoplay, directLink } = options ?? {};
        const sourceUrl = new URL(/^https?:\/\//i.test(url) ? url : `https://${url}`);
        let id = "";
        if (sourceUrl.hostname.includes("youtu.be")) {
            id = sourceUrl.pathname.slice(1);
        } else if (sourceUrl.searchParams.has("v")) {
            id = sourceUrl.searchParams.get("v") || "";
        }

        if (directLink) {
            const directLinkParameters = new URLSearchParams({ v: id });
            if (start && start > 0) directLinkParameters.set("t", `${start}s`);
            // YouTube does not support "end" on watch pages. Anymore? I am sure I remember that.
            return `https://www.youtube.com/watch?${directLinkParameters.toString()}`;
        }

        const embedParameters = new URLSearchParams();
        if (start && start > 0) embedParameters.set("start", String(Math.floor(start)));
        if (end && end !== 0) embedParameters.set("end", String(Math.floor(end)));
        if (hideControls) {
            embedParameters.set("controls", "0");
            embedParameters.set("modestbranding", "1");
            embedParameters.set("rel", "0");
        }
        if (autoplay) {
            embedParameters.set("autoplay", "1");
        }
        return `https://www.youtube.com/embed/${id}?${embedParameters.toString()}`;
    } catch {
        return url;
    }
}





interface ChatMessageVideoElementProps {
    xml: string;
}

export function ChatMessageVideoElement({xml}: ChatMessageVideoElementProps): JSX.Element {
    const [description, setDescription] = useState<string>("");
    const [videoSrc, setVideoSrc] = useState<string>("");
    const [videoStartPoint, setVideoStartPoint] = useState<number>(0);
    const [videoEndPoint, setVideoEndPoint] = useState<number>(0);
    const [videoDuration, setVideoDuration] = useState<number>(0);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const isYouTube = useMemo(() => isYouTubeUrl(videoSrc), [videoSrc]);


    useEffect(() => {
        extractXmlDetails(xml);
    }, [xml]);



    function handlePlay(): void {
        setIsModalOpen(true);
    }

    function handleModalClose(): void {
        setIsModalOpen(false);
    }




    function extractXmlDetails(xml: string): void {
        setDescription(extractInnerTag(xml, "video-description").trim());
        setVideoSrc(extractInnerTag(xml, "video-link").trim());
        updateVideoPointsFromXml(xml);
    }


    function extractInnerTag(block: string, tag: string): string {
        const regExPattern = new RegExp(`<\\s*${tag}\\b[^>]*>([\\s\\S]*?)<\\/\\s*${tag}\\s*>`, "i");
        const foundMatch = block.match(regExPattern);
        return foundMatch?.[1] ?? "";
    }


    function updateVideoPointsFromXml(xml: string): void {

        function setBothZero(): void {
            setVideoStartPoint(0);
            setVideoEndPoint(0);
        }

        const foundMatch = xml.match(/<\s*timestamp\b[^>]*>([\s\S]*?)<\/\s*timestamp\s*>/i);
        if (!foundMatch) { setBothZero(); return; }
        const raw = (foundMatch[1] ?? "").trim();
        if (!raw) { setBothZero(); return; }

        // 2) extract scalar tokens in order (numbers or min/max, quoted or not)
        //    Accepts: [[10, 20], ['min','max']], [[10],[min]], [10, min], etc.
        const tokenRegEx = /"(min|max)"|'(min|max)'|\bmin\b|\bmax\b|[+-]?\d+(?:\.\d+)?/gi;
        const tokens: string[] = [];
        let t: RegExpExecArray | null;
        while ((t = tokenRegEx.exec(raw)) !== null) {
            var token = t[0];
            // prefer the captured group value if present (to normalize quotes)
            if (t[1]) token = t[1]; else if (t[2]) token = t[2];
            tokens.push(token);
            if (tokens.length >= 2) break; // we only need a tuple
        }

        // Must be exactly a tuple (2 tokens). Otherwise, reject → set (0,0).
        if (tokens.length !== 2) { setBothZero(); return; }

        function coerce(token: string): number | null {
            var lower = token.replace(/^['"]|['"]$/g, "").toLowerCase();
            if (lower === "min") return 0;
            if (lower === "max") return Number.POSITIVE_INFINITY;
            if (/^[+-]?\d+(?:\.\d+)?$/.test(lower)) return Number(lower);
            return null; // invalid scalar
        }

        var start = coerce(tokens[0]);
        var end = coerce(tokens[1]);

        if (start === null || end === null) { setBothZero(); return; }

        setVideoStartPoint(start);
        setVideoEndPoint(end);
    }



    function isYouTubeUrl(url: string): boolean {
        if (!url) return false;
        try {
            const normalized = /^https?:\/\//i.test(url) ? url : `https://${url}`;
            const host = new URL(normalized).hostname.replace(/^www\./i, "");
            return host === "youtube.com" || host === "youtu.be" || host.endsWith(".youtube.com");
        } catch {
            return false;
        }
    }

    function getDomain(url: string, hideSubdomain = false): string {
        try {
            const normalized = url.match(/^https?:\/\//i) ? url : `https://${url}`;
            const normalizedUrl = new URL(normalized);
            const host = normalizedUrl.hostname;
            if (!hideSubdomain) return host;
            const parts = host.split(".");
            if (parts.length <= 2) return host;
            return parts.slice(-2).join(".");
        } catch {
            return url;
        }
    }

    function formatDuration(totalSeconds: number): string {
        var s = Math.max(0, Math.floor(totalSeconds));
        var h = Math.floor(s / 3600);
        var m = Math.floor((s % 3600) / 60);
        var sec = s % 60;
        var pad = (n: number) => (n < 10 ? "0" + n : String(n));
        return h > 0 ? `${h}:${pad(m)}:${pad(sec)}` : `${m}:${pad(sec)}`;
    }



    return (
        <div className="chat-message-video-element-container">
            
            <ChatMessageVideoElementModal
                isOpen={isModalOpen}
                onClose={handleModalClose}
                videoSrc={videoSrc}
                description={description}
                videoStartPoint={videoStartPoint}
                videoEndPoint={videoEndPoint}
                videoDuration={videoDuration}
                isYouTube={isYouTube}
            />

            <div className="video-background">

                <div className="video-container">

                    {videoSrc && isYouTube ?
                        <iframe
                            className="chat-message-video-element-player"
                            src={normalizeYouTubeUrl(videoSrc, { start: videoStartPoint, end: videoEndPoint, hideControls: true })}
                            title="YouTube video"
                            allow="clipboard-write; encrypted-media;"
                        />
                    :
                        <video
                            className="chat-message-video-element-player"
                            src={videoSrc}
                            preload="metadata"
                            onLoadedMetadata={(event) => {
                                const video = event.currentTarget;
                                setVideoDuration(video.duration);
                                if (videoStartPoint > 0) video.currentTime = videoStartPoint;
                            }}
                        >
                            Your browser doesn't support embedded videos.
                        </video>                    
                    }


                    <div className="video-overlay-container">
                        {!isYouTube ? undefined :
                            <div className="youtube-button">
                                <CommonButton onClick={handlePlay} className="play-button" noBackground>
                                    <ElevaiteIcons.SVGPlay/>
                                </CommonButton>
                            </div>
                        }

                        <div className="overlay-interactions-container">
                            {isYouTube ? undefined :
                                <CommonButton onClick={handlePlay} className="play-button" noBackground>
                                    <ElevaiteIcons.SVGPlay/>
                                </CommonButton>
                            }

                            {!videoDuration ? undefined :
                                <div className="playtime-container">
                                    {formatDuration(videoDuration)}
                                </div>
                            }
                        </div>

                        <div className="overlay-details-container">
                            <span className="video-description">
                                {description}
                            </span>
                            <div className="source-details">
                                {!isYouTube ? undefined :
                                    <div className="youtube-icon">
                                        <Logos.Youtube/>
                                    </div>
                                }
                                <span>{getDomain(videoSrc, true)}</span>
                            </div>
                        </div>

                    </div>

                </div>

            </div>
        </div>
    );
}





















