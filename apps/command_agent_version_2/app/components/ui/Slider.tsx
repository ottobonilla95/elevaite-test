import { useEffect, useMemo, useRef, useState, type JSX } from "react";
import "./Slider.scss";
import { cls } from "@repo/ui";
import { CommonButton, CommonInput } from "@repo/ui/components";


type SliderType = "input" | "bar" | "both";

interface SliderProps {
    label?: string;
    type?: SliderType;
    value: number;
    onChange?: (value: number) => void;
    min?: number;
    max?: number;
    step?: number;
    decimals?: number;
    allowNegative?: boolean;
    showInputArrows?: boolean;
    showInput?: boolean;
    showBar?: boolean;
    startLabel?: string;
    endLabel?: string;
    inputWidthPx?: number;
    disabled?: boolean;
}

export function Slider(props: SliderProps): JSX.Element {
    const { label, type, value, onChange, min, max, step, decimals, allowNegative, showInputArrows, startLabel, endLabel, inputWidthPx, disabled, ...rest } = props;    
    const barRef = useRef<HTMLDivElement | null>(null);
    const isDraggingRef = useRef<boolean>(false);
    const resolvedType: SliderType = type ?? "both";
    const resolvedMin = min ?? 0;
    const resolvedMax = max ?? 1;
    const resolvedStep = step ?? 0.1;
    const resolvedShowInput = resolvedType === "input" || resolvedType === "both";
    const resolvedShowBar = resolvedType === "bar" || resolvedType === "both";
    const resolvedShowInputArrows = showInputArrows ?? true;
    const resolvedInputWidthPx = inputWidthPx ?? 72;

    const resolvedDecimals = useMemo<number>(() => {
        if (typeof decimals === "number") return Math.max(0, decimals);
        return countDecimals(resolvedStep);
    }, [decimals, resolvedStep]);

    const resolvedAllowNegative = useMemo<boolean>(() => {
        if (typeof allowNegative === "boolean") return allowNegative;
        return resolvedMin < 0;
    }, [allowNegative, resolvedMin]);

    const [inputText, setInputText] = useState<string>(() => String(value));



    useEffect(() => {
        // Keep input text synced unless the user is mid-edit with non-numeric text
        if (!Number.isFinite(value)) return;
        const next = resolvedDecimals > 0 ? value.toFixed(resolvedDecimals) : String(Math.trunc(value));
        setInputText(next);
    }, [value, resolvedDecimals]);




    function commit(nextValue: number): void {
        if (disabled) return;
        const clamped = clamp(nextValue, resolvedMin, resolvedMax);
        const snapped = snapToStep(clamped, resolvedMin, resolvedStep, resolvedDecimals);
        if (onChange) onChange(snapped);
    }

    function adjustBy(deltaSteps: number): void {
        const next = value + deltaSteps * resolvedStep;
        commit(next);
    }

    function parseInputToNumber(text: string): number | undefined {
        const trimmed = text.trim();
        if (!trimmed) return undefined;

        // allow " - ", "-.", ".", etc while typing without committing
        if (trimmed === "-" || trimmed === "." || trimmed === "-.") return undefined;

        const parsed = Number(trimmed);
        if (!Number.isFinite(parsed)) return undefined;

        if (!resolvedAllowNegative && parsed < 0) return 0;
        return parsed;
    }

    function handleInputChange(nextText: string): void {
        if (disabled) return;
        setInputText(nextText);
    }

    function handleInputBlur(): void {
        const parsed = parseInputToNumber(inputText);
        if (parsed === undefined) {
            const next = resolvedDecimals > 0 ? value.toFixed(resolvedDecimals) : String(Math.trunc(value));
            setInputText(next);
            return;
        }
        commit(parsed);
    }

    function handleInputKeyDown(key: string): void {
        if (disabled) return;

        if (key === "Enter") {
            handleInputBlur();
            return;
        }
        if (key === "ArrowUp") {
            adjustBy(1);
            return;
        }
        if (key === "ArrowDown") {
            adjustBy(-1);
        }
    } 

    function getBarPercentFromValue(v: number): number {
        if (resolvedMax <= resolvedMin) return 0;
        const t = (v - resolvedMin) / (resolvedMax - resolvedMin);
        return clamp(t, 0, 1);
    }

    function getValueFromClientX(clientX: number): number | undefined {
        if (!barRef.current) return undefined;
        const rect = barRef.current.getBoundingClientRect();
        const x = clamp(clientX - rect.left, 0, rect.width);
        const t = rect.width <= 0 ? 0 : x / rect.width;
        const next = resolvedMin + t * (resolvedMax - resolvedMin);
        return next;
    }


    function handleBarPointerDown(event: React.PointerEvent<HTMLDivElement>): void {
        if (disabled) return;
        isDraggingRef.current = true;
        event.preventDefault();
        event.currentTarget.setPointerCapture(event.pointerId);
        const next = getValueFromClientX(event.clientX);
        if (next !== undefined) commit(next);
    }

    function handleBarPointerMove(event: React.PointerEvent<HTMLDivElement>): void {
        if (disabled) return;
        if (!isDraggingRef.current) return;

        const next = getValueFromClientX(event.clientX);
        if (next !== undefined) commit(next);
    }

    function handleBarPointerUp(event: React.PointerEvent<HTMLDivElement>): void {
        if (disabled) return;
        isDraggingRef.current = false;
        try {
            event.currentTarget.releasePointerCapture(event.pointerId);
        } catch {
            // ignore
        }
    }

    const percent = getBarPercentFromValue(value);
    const shouldRenderTopRow = Boolean(label) || resolvedShowInput;
    const shouldRenderInput = resolvedShowInput;
    const shouldRenderBar = resolvedShowBar;





    return (
        <div
            className={cls("slider-container", disabled && "disabled")}
            {...rest}
        >
            {!shouldRenderTopRow ? null : (
                <div className="top-row">
                {!label ? <div className="label-spacer" /> : <div className="label">{label}</div>}

                {!shouldRenderInput ? null : (
                    <div className="input-group" onBlurCapture={handleInputBlur}>
                    <div className="number-input-wrapper" style={{ width: resolvedInputWidthPx }}>
                        <CommonInput
                            className="number-input"
                            controlledValue={inputText}
                            onChange={handleInputChange}
                            onKeyDown={handleInputKeyDown}
                            disabled={disabled}
                        />
                    </div>

                    {!resolvedShowInputArrows ? null : (
                        <div className="steppers" aria-hidden="true">
                        <CommonButton
                            className="step-button"
                            onClick={() => { adjustBy(1); }}
                            disabled={disabled}
                            title="Increase"
                            noBackground
                        >
                            ▲
                        </CommonButton>
                        <CommonButton
                            className="step-button"
                            onClick={() => { adjustBy(-1); }}
                            disabled={disabled}
                            title="Decrease"
                            noBackground
                        >
                            ▼
                        </CommonButton>
                        </div>
                    )}
                    </div>
                )}
                </div>
            )}

            {!shouldRenderBar ? null : (
                <div className="bar-row">
                    <div
                        ref={barRef}
                        className="bar"
                        role="slider"
                        onPointerDown={handleBarPointerDown}
                        onPointerMove={handleBarPointerMove}
                        onPointerUp={handleBarPointerUp}
                        onPointerCancel={handleBarPointerUp}
                        aria-valuemin={resolvedMin}
                        aria-valuemax={resolvedMax}
                        aria-valuenow={value}
                        tabIndex={disabled ? -1 : 0}
                    >
                        <div className="track" />
                        <div className="fill" style={{ width: `${(percent * 100).toString()}%` }} />
                        <div className="handle" style={{ left: `${(percent * 100).toString()}%` }} />
                    </div>
                    {!startLabel && !endLabel ? null : (
                        <div className="bar-labels">
                            <div className="bar-label start">{startLabel}</div>
                            <div className="bar-label end">{endLabel}</div>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}



function clamp(value: number, min: number, max: number): number {
    return Math.min(max, Math.max(min, value));
}

function countDecimals(value: number): number {
    if (!Number.isFinite(value)) return 0;
    const text = value.toString();
    if (!text.includes(".")) return 0;
    return text.split(".")[1]?.length ?? 0;
}

function roundTo(value: number, decimals: number): number {
    if (decimals <= 0) return Math.round(value);
    const p = Math.pow(10, decimals);
    return Math.round(value * p) / p;
}

function snapToStep(value: number, min: number, step: number, decimals: number): number {
    if (step <= 0) return roundTo(value, decimals);
    const snapped = min + Math.round((value - min) / step) * step;
    return roundTo(snapped, decimals);
}