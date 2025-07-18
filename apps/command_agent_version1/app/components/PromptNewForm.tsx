import { CommonSelect, type CommonSelectOption, SimpleInput, SimpleTextarea } from "@repo/ui/components";
import React, { useEffect, useRef, useState } from "react";
import { createPortal } from 'react-dom';
import RangeSlider from 'react-range-slider-input';
import 'react-range-slider-input/dist/style.css';
import { type NewPromptInputExecution, type NewPromptInputOutputFormat, type NewPromptInputParameter, type NewPromptInputSelectedModelOnHover, type NewPromptInputStatus, type NewPromptInputVersion } from "../lib/interfaces";
import PromptMultiTagInputs from "./PromptMultiTagInputs";

const parameters: CommonSelectOption[] = [
	{ value: 'Parameters', disabled: true },
	{ value: 'None'}
];

const statuses: CommonSelectOption[] = [
	{ value: 'Status', disabled: true },
	{ value: 'Draft'},
	{ value: 'In Review'},
	{ value: 'Approved'},
];

const models: CommonSelectOption[] = [
	{ value: 'Model', disabled: true },
	{ value: 'Open AI', label: 'Open AI', isSeparator: true },
	{ value: 'GPT4o-Mini'},
	{ value: 'GPT 4 Turbo'},
	{ value: 'Anthropic', label: 'Anthropic', isSeparator: true },
	{ value: 'Claude 3.5 Sonet'},
	{ value: 'Claude 3 Opus'},
];

const availableModels: NewPromptInputSelectedModelOnHover[] = [
	{ id: 'GPT4o-Mini', name: 'GPT 4', description: 'GPT 4 from OpenAI has broad general knowledge and domain expertise allowing it to follow complex instructions in natural language and solve difficult problems accurately.', context: '8,192 tokens', inputPricing: '$30.00/ 1M tokens', outputPricing: '$60.00/ 1M tokens' },
	{ id: 'GPT 4 Turbo', name: 'GPT 4', description: 'GPT 4 from OpenAI has broad general knowledge and domain expertise allowing it to follow complex instructions in natural language and solve difficult problems accurately.', context: '8,192 tokens', inputPricing: '$30.00/ 1M tokens', outputPricing: '$60.00/ 1M tokens' },
	{ id: 'Claude 3.5 Sonet', name: 'Claude 3.5', description: 'GPT 4 from OpenAI has broad general knowledge and domain expertise allowing it to follow complex instructions in natural language and solve difficult problems accurately.', context: '8,192 tokens', inputPricing: '$30.00/ 1M tokens', outputPricing: '$60.00/ 1M tokens' },
	{ id: 'Claude 3 Opus', name: 'Claude 3', description: 'GPT 4 from OpenAI has broad general knowledge and domain expertise allowing it to follow complex instructions in natural language and solve difficult problems accurately.', context: '8,192 tokens', inputPricing: '$30.00/ 1M tokens', outputPricing: '$60.00/ 1M tokens' },
];

const versions: CommonSelectOption[] = [
	{ value: 'Version', disabled: true },
];

const executions: CommonSelectOption[] = [
	{ value: 'Hosted'},
	{ value: 'Custom API'},
];

const outputs: CommonSelectOption[] = [
	{ value: 'JSON'},
	{ value: 'CSV'},
	{ value: 'HTML'},
];

function PromptNewForm(): React.ReactElement {
	const [name, setName] = useState("");
	const [tags, setTags] = useState<string[]>([]);
	const [description, setDescription] = useState("");
	const [parameter, setParameter] = useState<NewPromptInputParameter>("Parameters");
	const [status, setStatus] = useState<NewPromptInputStatus>("Status");
	const [version, setVersion] = useState<NewPromptInputVersion>("Version");
	const [model, setModel] = useState("Model");
	const [execution, setExecution] = useState<NewPromptInputExecution>("Hosted");
	const [outputFormat, setOutputFormat] = useState<NewPromptInputOutputFormat>("JSON");
	const [temperature, setTemperature] = useState("0");
	const [maxTokens, setMaxTokens] = useState("0");
	const [selectedModelOnHover, setSelectedModelOnHover] = useState("");

	const [showHover, setShowHover] = useState(false);
  	const [hoverPosition, setHoverPosition] = useState<{top: number, left: number}>({top: 0, left: 0});
	const hoverTargetRef = useRef<HTMLDivElement | null>(null);
	const [portalRoot, setPortalRoot] = useState<HTMLElement | null>(null);


	useEffect(() => {
		setPortalRoot(document.getElementById("portal-root"));
	}, []);

	useEffect(() => {
		function updatePosition(): void {
			if (hoverTargetRef.current) {
				const rect = hoverTargetRef.current.getBoundingClientRect();

				setHoverPosition({
					top: rect.bottom + window.scrollY,
					left: rect.left + 400 + window.scrollX
				});
			}
		}

		if(showHover) {
			updatePosition();
			window.addEventListener('scroll', updatePosition);
			window.addEventListener('resize', updatePosition);

			return () => {
				window.removeEventListener('scroll', updatePosition);
				window.removeEventListener('resize', updatePosition);
			};
		}
	}, [showHover]);

	const selectedModelObject = availableModels.find(foundModel => foundModel.id === selectedModelOnHover);

	const handleNameChange = (text: string): void => {
		setName(text);
	}

	const handleDescriptionChange = (text: string): void => {
		setDescription(text);
	}

	const handleParameterChange = (text: NewPromptInputParameter): void => {
		setParameter(text);
	}

	const handleStatusChange = (text: NewPromptInputStatus): void => {
		setStatus(text);
	}

	const handleVersionChange = (text: NewPromptInputVersion): void => {
		setVersion(text);
	}

	const handleModelChange = (text: string): void => {
		setModel(text);
	}

	const handleModelOnHover = (text: string): void => {
		setShowHover(true);
		setSelectedModelOnHover(text);
	}

	const handleModelOnLeave = (): void => {
		setShowHover(false);
		setSelectedModelOnHover("");
	}

	const handleExecutionChange = (text: NewPromptInputExecution): void => {
		setExecution(text);
	}

	const handleOutputChange = (text: NewPromptInputOutputFormat): void => {
		setOutputFormat(text);
	}

	const handleTagsChange = (passedTags: string[]): void => {
		setTags(passedTags);
	}

	const handleTemperatureChange = (text: string): void => {
		setTemperature(text);
	}

	const handleMaxTokensChange = (text: string): void => {
		setMaxTokens(text);
	}

	const handleRangeSliderTemperatureChange = (value: number[]): void => {
		setTemperature(value[1].toString());
	}

	const handleRangeSliderMaxTokensChange = (value: number[]): void => {
		setMaxTokens(value[1].toString());
	}


  return (
	<div className="flex flex-col w-full">
		<div className="flex-1">
			<div className="py-4 flex items-center justify-between">
				<div className="font-medium">
					Edit Prompt
				</div>

				<div className="flex items-center gap-3">
					{/* <button>
						<svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
							<g opacity="0.8">
								<path d="M8.00004 8.66663C8.36823 8.66663 8.66671 8.36815 8.66671 7.99996C8.66671 7.63177 8.36823 7.33329 8.00004 7.33329C7.63185 7.33329 7.33337 7.63177 7.33337 7.99996C7.33337 8.36815 7.63185 8.66663 8.00004 8.66663Z" stroke="#212124" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
								<path d="M8.00004 3.99996C8.36823 3.99996 8.66671 3.70148 8.66671 3.33329C8.66671 2.9651 8.36823 2.66663 8.00004 2.66663C7.63185 2.66663 7.33337 2.9651 7.33337 3.33329C7.33337 3.70148 7.63185 3.99996 8.00004 3.99996Z" stroke="#212124" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
								<path d="M8.00004 13.3333C8.36823 13.3333 8.66671 13.0348 8.66671 12.6666C8.66671 12.2984 8.36823 12 8.00004 12C7.63185 12 7.33337 12.2984 7.33337 12.6666C7.33337 13.0348 7.63185 13.3333 8.00004 13.3333Z" stroke="#212124" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
							</g>
						</svg>
					</button> */}
				</div>
			</div>
			<div className="prompt-form">
				<div className="mb-4">
					<label className="inline-block text-sm font-medium mb-2" htmlFor="name">Prompt Name</label>
					<div className="prompt-input-container no-margin rounded-md">
						<SimpleInput id="name" wrapperClassName="prompt-input" value={name} placeholder="e.g. Invoice Analyzer" useCommonStyling onChange={handleNameChange} />
					</div>
				</div>
				<div className="mb-4">
					<span className="inline-block text-sm font-medium mb-2">Tags</span>
					<div className="prompt-input-container prompt-multi-tag-container no-margin rounded-md">
						<PromptMultiTagInputs onChange={handleTagsChange} />
					</div>
				</div>
				<div className="mb-4">
					<label className="inline-block text-sm font-medium mb-2" htmlFor="description">Description</label>
					<div className="prompt-input-container prompt-textarea-container no-margin">
						<SimpleTextarea id="description" wrapperClassName="prompt-input" value={description} placeholder="e.g. Extracts information from invoices" useCommonStyling onChange={handleDescriptionChange} />
					</div>
				</div>
				<div className="grid grid-cols-2 gap-4 mb-4">
					<div className="prompt-input-container prompt-select-container no-margin rounded-md">
						<CommonSelect defaultValue={status} options={statuses} onSelectedValueChange={handleStatusChange} />
					</div>
					<div className="prompt-input-container prompt-select-container no-margin rounded-md">
						<CommonSelect defaultValue={version} options={versions} onSelectedValueChange={handleVersionChange} />
					</div>
				</div>
				<hr className="mb-4" />
				<div className="mb-4 relative">
					<div
					ref={hoverTargetRef} className="prompt-select-container-hover prompt-input-container prompt-select-container no-margin rounded-md">
						<CommonSelect defaultValue={model} options={models} onSelectedValueChange={handleModelChange} onHover={handleModelOnHover} onLeave={handleModelOnLeave} />
					</div>
					{showHover && portalRoot ? createPortal(
						<div className="card-on-hover text-sm p-3 absolute w-[270px] bg-white rounded-xl" style={{ zIndex: 100, top: hoverPosition.top, left: hoverPosition.left }}>
							<div className="font-semibold">
								{selectedModelObject?.name}
							</div>
							<div className="mt-3 mb-4">
								{selectedModelObject?.description}
							</div>
							<div>
								<div className="flex justify-between mb-2">
									<span className="font-semibold">Context</span>
									{selectedModelObject?.context}
								</div>
								<div className="flex justify-between mb-2">
									<span className="font-semibold">Input Pricing</span>
									{selectedModelObject?.inputPricing}
								</div>
								<div className="flex justify-between mb-2">
									<span className="font-semibold">Output Pricing</span>
									{selectedModelObject?.outputPricing}
								</div>
							</div>
						</div>,
						portalRoot
					) : null}
				</div>
				<div className="mb-4">
					<div className="prompt-input-container prompt-select-container no-margin rounded-md">
						<CommonSelect defaultValue={parameter} options={parameters} onSelectedValueChange={handleParameterChange} />
					</div>
				</div>
				<div className="grid grid-cols-2 gap-4 mb-4">
					<div>
						<label className="inline-block text-sm font-medium mb-2" htmlFor="description">Execution</label>
						<div className="prompt-input-container prompt-select-container no-margin rounded-md">
							<CommonSelect id="execution" defaultValue={execution} options={executions} onSelectedValueChange={handleExecutionChange} />
						</div>
					</div>
					<div>
						<label className="inline-block text-sm font-medium mb-2" htmlFor="description">Output</label>
						<div className="prompt-input-container prompt-select-container no-margin rounded-md">
							<CommonSelect id="output" defaultValue={outputFormat} options={outputs} onSelectedValueChange={handleOutputChange} />
						</div>
					</div>
				</div>
				<div className="mb-4">
					<label className="inline-block text-sm font-medium mb-2" htmlFor="temperature">Temperature</label>
					<div className="prompt-input-container no-margin rounded-md">
						<SimpleInput id="temperature" type="number" wrapperClassName="prompt-input" value={temperature} useCommonStyling onChange={handleTemperatureChange} />
					</div>
					<div className="mt-5 my-4">
						<RangeSlider className="prompt-input-range-slider" value={[0, Number(temperature)]} min={0} max={1} step={0.1} onInput={handleRangeSliderTemperatureChange} />
						<div className="flex justify-between text-xs mt-3">
							<span>Predictable</span>
							<span>Creative</span>
						</div>
					</div>
				</div>
				<div className="mb-4">
					<label className="inline-block text-sm font-medium mb-2" htmlFor="temperature">Max Tokens</label>
					<div className="prompt-input-container no-margin rounded-md">
						<SimpleInput id="max-tokens" type="number" wrapperClassName="prompt-input" value={maxTokens} useCommonStyling onChange={handleMaxTokensChange} />
					</div>
					<div className="mt-5 my-4">
						<RangeSlider className="prompt-input-range-slider" value={[0, Number(maxTokens)]} min={0} max={2000} step={100} onInput={handleRangeSliderMaxTokensChange} />
						<div className="flex justify-between text-xs mt-3">
							<span>Small Content</span>
							<span>Large Content</span>
						</div>
					</div>
				</div>
			</div>
		</div>

		<div className="grid gap-3 justify-end my-5" style={{ gridTemplateColumns: 'auto auto' }}>
			<button type="button" className="btn btn-outline disabled:bg-gray-100 disabled:text-gray-400 disabled:hover:bg-gray-100 disabled:hover:text-gray-400">
				Cancel
			</button>
			<button type="button" className="btn btn-primary disabled:bg-gray-100 disabled:text-gray-400 disabled:hover:bg-gray-100 disabled:hover:text-gray-400">
				Save
			</button>
		</div>
	</div>
  )
}
export default PromptNewForm