"use client";
import { useEffect, useRef } from "react";



function useOutsideDetector (
	ref: React.MutableRefObject<HTMLElement | null>,
	onOutsideClick: (event: MouseEvent) => void,
	options: {
		isDisabled?: boolean,
		ignoredRefs?: [React.MutableRefObject<HTMLElement | null>]
	},
) {
	useEffect(() => {
		function handleClickOutside(event: MouseEvent) {
            // console.log('ignored refs', options.ignoredRefs);
			if ( ref.current && !ref.current.contains(event.target as Node) ) {
				if ( options.ignoredRefs && options.ignoredRefs.findIndex(ref => ref.current?.contains(event.target as Node)) > -1 ) {
					// The click is outside the designated area BUT inside a ref we're instructed to ignore.
					return;
				}
				onOutsideClick(event);
			}
		}

		if (!options.isDisabled)
			document.addEventListener('mouseup', handleClickOutside);

		return () => {
			document.removeEventListener('mouseup', handleClickOutside);
		};
	}, [ref, options]);
}


interface ClickOutsideDetectorProps {
	onOutsideClick: (event: MouseEvent) => void;
	children?: React.ReactNode;
	disabled?: boolean;
	ignoredRefs?: [React.MutableRefObject<HTMLElement | null>];
}

export function ClickOutsideDetector(props: ClickOutsideDetectorProps): React.ReactElement {
	const wrapperRef = useRef<HTMLElement | null>(null);
	useOutsideDetector(wrapperRef, props.onOutsideClick, { isDisabled: props.disabled, ignoredRefs: props.ignoredRefs });

	return (
		<section ref={ wrapperRef } style={ { display: 'contents' } }>
			{ props.children }
		</section>
	);
}
