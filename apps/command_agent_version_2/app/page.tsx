import { CanvasContainer } from "./components/CanvasContainer";
import "./page.scss";

import type { JSX } from "react";

export default function CommandAgent(): JSX.Element {
	return (
		<main className="agent-version-2-main-container">
			<CanvasContainer/>
		</main>
	);
}