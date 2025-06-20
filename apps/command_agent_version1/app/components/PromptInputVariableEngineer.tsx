<<<<<<< HEAD
import { CommonCheckbox, CommonSelect, CommonSelectOption, SimpleInput, SimpleTextarea } from "@repo/ui/components"
import { usePrompt } from "../ui/contexts/PromptContext";
import { PromptInputVariableEngineerItem, PromptInputVariableEngineerType } from "../lib/interfaces";
import { useEffect, useState } from "react";
import PromptMultiTagInputs from "./PromptMultiTagInputs";
=======
import { CommonSelect, CommonSelectOption, SimpleInput, SimpleTextarea } from "@repo/ui/components"
import { usePrompt } from "../ui/contexts/PromptContext";
import { PromptInputVariableEngineerItem, PromptInputVariableEngineerType } from "../lib/interfaces";
import { useState } from "react";
>>>>>>> 243bfb16 (create new prompt engineer page & fix conflicts)

type PromptInputVariableEngineerProps = PromptInputVariableEngineerItem;

const PromptInputVariableEngineer = (props: PromptInputVariableEngineerProps) => {
	const [name, setName] = useState("");
	const [displayName, setDisplayName] = useState("");
<<<<<<< HEAD
	const [type, setType] = useState<PromptInputVariableEngineerType>("String");
	const [required, setRequired] = useState(true);
	const [json, setJson] = useState(true);
	const [definition, setDefinition] = useState("");
	const [values, setValues] = useState<string[]>([]);
	const allFilled = name && displayName;
	const [edit, setEdit] = useState(false);

	const promptContext = usePrompt();

	useEffect(() => {
		console.log('Required: ', required, 'JSON: ', json);
	}, [required, json]);

	useEffect(() => {
		if (!edit) {
			const selectedVariable = promptContext.promptInputVariablesEngineer.find(variable => variable.id === props.id);
			setName(selectedVariable?.name || "");
			setDisplayName(selectedVariable?.displayName || "");
			setType(selectedVariable?.type || "String");
			setRequired(selectedVariable?.required ?? true);
			setJson(selectedVariable?.json ?? true);
			setDefinition(selectedVariable?.definition || "");
			setValues(selectedVariable?.values || []);
		}
	}, [promptContext.promptInputVariablesEngineer]);

	const variableTypes: CommonSelectOption[] = [
		{ value: 'String'},
		{ value: 'Array of Strings'},
		{ value : 'JSON' },
		{ value : 'JSON to HTML' },
		{ value : 'Markdown to HTML' }
	];

	const handleSaveVariable = () => {
		let updatedDefinition = definition;
    	let updatedValues = values;

		if (type === "Array of Strings") {
			updatedDefinition = "";
		} else if (type === "String") {
			updatedValues = [];
		}

=======
	const [type, setType] = useState<PromptInputVariableEngineerType>("Text");
	const [required, setRequired] = useState(true);
	const [json, setJson] = useState(true);
	const [definition, setDefinition] = useState("");
	const allFilled = name && displayName && definition;

	const promptContext = usePrompt();

	const variableTypes: CommonSelectOption[] = [
		{ value: 'String', label: "String" },
		{ value: 'Text', label: "Text" },
		{ value: 'TeaxtArea', label: "TeaxtArea" },
	];

	const handleSaveVariable = () => {
>>>>>>> 243bfb16 (create new prompt engineer page & fix conflicts)
		const updates: PromptInputVariableEngineerItem = {
			id: props.id,
			name,
			displayName,
			type,
			required,
			json,
<<<<<<< HEAD
			definition: updatedDefinition,
        	values: updatedValues,
			saved: true,
		}
		promptContext.savePromptInputVariableEngineer(props.id, updates);

		setDefinition(updatedDefinition);
    	setValues(updatedValues);
	}

	const handleEditVariable = () => {
		setEdit(true);
		promptContext.editPromptInputVariableEngineer(props.id);
	}

	const handleCancelEditVariable = () => {
		const selectedVariable = promptContext.promptInputVariablesEngineer.find(variable => variable.id === props.id);
		setName(selectedVariable?.name || "");
		setDisplayName(selectedVariable?.displayName || "");
		setType(selectedVariable?.type || "String");
		setRequired(selectedVariable?.required ?? true);
		setJson(selectedVariable?.json ?? true);
		setDefinition(selectedVariable?.definition || "");
		setValues(selectedVariable?.values || []);

		promptContext.savePromptInputVariableEngineer(props.id, { saved: true });
	}

=======
			definition,
			saved: true,
		}
		promptContext.savePromptInputVariableEngineer(props.id, updates);
	}

	const handleEditVariable = () => {
		promptContext.editPromptInputVariableEngineer(props.id);
	}

>>>>>>> 243bfb16 (create new prompt engineer page & fix conflicts)
	const handleRemoveVariable = () => {
		promptContext.removePromptInputVariableEngineer(props.id);
	}

<<<<<<< HEAD
	const handleNameChange = (text: string) => {
		setName(text)
	}

	const handleDisplayNameChange = (text: string) => {
		setDisplayName(text);
	}

	const handleTypeChange = (text: PromptInputVariableEngineerType) => {
		setType(text);
	}

	const handleRequiredChange = (value: boolean) => {
		setRequired(value);
	}

	const handleJsonChange = (value: boolean) => {
		setJson(value);
	}

	const handleDefinitionChange = (text: string) => {
		setDefinition(text);
	}

=======
>>>>>>> 243bfb16 (create new prompt engineer page & fix conflicts)
  return (
	<>
		{props.saved ? (
			<div className="card-variable prompt-input-container">
				<div className="prompt-input-header flex items-center justify-between" style={{padding: '16px'}}>
					<div className="flex items-center gap-2">
						<div>{props.name}</div>
<<<<<<< HEAD
						<button onClick={handleEditVariable} title="Edit Variable">
=======
						<button onClick={handleEditVariable}>
>>>>>>> 243bfb16 (create new prompt engineer page & fix conflicts)
							<svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
								<path d="M14.0003 14H8.66701M1.66699 14.3334L5.36651 12.9105C5.60313 12.8195 5.72145 12.774 5.83214 12.7146C5.93046 12.6618 6.02419 12.6009 6.11235 12.5324C6.21161 12.4554 6.30124 12.3658 6.48051 12.1865L14.0003 4.66671C14.7367 3.93033 14.7367 2.73642 14.0003 2.00004C13.264 1.26366 12.0701 1.26366 11.3337 2.00004L3.81385 9.51985C3.63458 9.69912 3.54494 9.78876 3.46792 9.88801C3.39951 9.97617 3.33859 10.0699 3.28582 10.1682C3.2264 10.2789 3.18089 10.3972 3.08988 10.6339L1.66699 14.3334ZM1.66699 14.3334L3.03907 10.766C3.13726 10.5107 3.18635 10.3831 3.27055 10.3246C3.34414 10.2735 3.43519 10.2542 3.52319 10.271C3.62388 10.2902 3.72058 10.3869 3.91398 10.5803L5.42004 12.0864C5.61344 12.2798 5.71014 12.3765 5.72937 12.4772C5.74617 12.5652 5.72685 12.6562 5.67576 12.7298C5.61729 12.814 5.48965 12.8631 5.23437 12.9613L1.66699 14.3334Z" stroke="#212124" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
							</svg>
						</button>
					</div>
<<<<<<< HEAD
					<button onClick={handleRemoveVariable} title="Remove Variable">
=======
					<button onClick={handleRemoveVariable}>
>>>>>>> 243bfb16 (create new prompt engineer page & fix conflicts)
						<svg width="17" height="16" viewBox="0 0 17 16" fill="none">
							<g opacity="0.8">
								<path d="M11.1667 4V3.46671C11.1667 2.71997 11.1667 2.3466 11.0213 2.06139C10.8935 1.8105 10.6895 1.60653 10.4387 1.4787C10.1534 1.33337 9.78007 1.33337 9.03333 1.33337H7.96667C7.21993 1.33337 6.84656 1.33337 6.56135 1.4787C6.31046 1.60653 6.10649 1.8105 5.97866 2.06139C5.83333 2.3466 5.83333 2.71997 5.83333 3.46671V4M7.16667 7.66671V11M9.83333 7.66671V11M2.5 4H14.5M13.1667 4V11.4667C13.1667 12.5868 13.1667 13.1469 12.9487 13.5747C12.7569 13.951 12.451 14.257 12.0746 14.4487C11.6468 14.6667 11.0868 14.6667 9.96667 14.6667H7.03333C5.91323 14.6667 5.35318 14.6667 4.92535 14.4487C4.54903 14.257 4.24307 13.951 4.05132 13.5747C3.83333 13.1469 3.83333 12.5868 3.83333 11.4667V4" stroke="#212124" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
							</g>
						</svg>
					</button>
				</div>
<<<<<<< HEAD
				{type === "String" && (
					<SimpleTextarea disabled wrapperClassName="prompt-input" value={definition} placeholder="{header / Customer / Product /Quantity / Invoice Amount}" useCommonStyling onChange={() => console.log("")} style={{filter: "none"}}></SimpleTextarea>
				)}
				{type === "Array of Strings" && (
					<PromptMultiTagInputs disabled values={values} onChange={setValues}/>
				)}
=======
				<SimpleTextarea disabled wrapperClassName="prompt-input" value={definition} placeholder="{header / Customer / Product /Quantity / Invoice Amount}" useCommonStyling onChange={() => console.log("")} style={{filter: "none"}}></SimpleTextarea>
>>>>>>> 243bfb16 (create new prompt engineer page & fix conflicts)
			</div>
		) : (
			<div className="card-variable card-variable-new rounded-xl" style={{border: '1px solid #E2E8ED'}}>
				<div className="rounded-lg bg-white" style={{border: '1px solid #E3E8EF', margin: '5px'}}>
					<div className="p-4">
						<div className="header flex items-center justify-between pb-4" style={{borderBottom: '1px solid #E3E8EF'}}>
							<div className="text-lg font-medium">{"" !== name ? name : 'New Variable'}</div>
							<div className="flex items-center gap-2">
<<<<<<< HEAD
								<button onClick={handleSaveVariable} disabled={!allFilled} title="Save Variable">
=======
								<button onClick={handleSaveVariable} disabled={!allFilled}>
>>>>>>> 243bfb16 (create new prompt engineer page & fix conflicts)
									<svg width="20" height="21" viewBox="0 0 20 21" fill="none" xmlns="http://www.w3.org/2000/svg">
										<path d="M16.8 5.69971L8 14.4997L4 10.4997" stroke="#FF681F" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/>
									</svg>
								</button>
<<<<<<< HEAD
								{edit && (
									<button onClick={handleCancelEditVariable} title="Cancel Edit">
										<svg width="12" height="13" viewBox="0 0 12 13" fill="none" xmlns="http://www.w3.org/2000/svg">
											<path d="M11 1.5L1 11.5M1 1.5L11 11.5" stroke="#FF681F" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"></path>
										</svg>
									</button>
								)}
								<button onClick={handleRemoveVariable} title="Remove Variable">
=======
								<button onClick={handleRemoveVariable}>
>>>>>>> 243bfb16 (create new prompt engineer page & fix conflicts)
									<svg width="17" height="16" viewBox="0 0 17 16" fill="none">
										<g opacity="0.8">
											<path d="M11.1667 4V3.46671C11.1667 2.71997 11.1667 2.3466 11.0213 2.06139C10.8935 1.8105 10.6895 1.60653 10.4387 1.4787C10.1534 1.33337 9.78007 1.33337 9.03333 1.33337H7.96667C7.21993 1.33337 6.84656 1.33337 6.56135 1.4787C6.31046 1.60653 6.10649 1.8105 5.97866 2.06139C5.83333 2.3466 5.83333 2.71997 5.83333 3.46671V4M7.16667 7.66671V11M9.83333 7.66671V11M2.5 4H14.5M13.1667 4V11.4667C13.1667 12.5868 13.1667 13.1469 12.9487 13.5747C12.7569 13.951 12.451 14.257 12.0746 14.4487C11.6468 14.6667 11.0868 14.6667 9.96667 14.6667H7.03333C5.91323 14.6667 5.35318 14.6667 4.92535 14.4487C4.54903 14.257 4.24307 13.951 4.05132 13.5747C3.83333 13.1469 3.83333 12.5868 3.83333 11.4667V4" stroke="#212124" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
										</g>
									</svg>
								</button>
							</div>
						</div>
						<div className="mt-4">
							<div className="grid grid-cols-2 gap-4 mb-4">
								<div>
									<label className="inline-block text-sm font-medium mb-2" htmlFor="variable-name">Variable Name</label>
									<div className="prompt-input-container no-margin rounded-md">
<<<<<<< HEAD
										<SimpleInput id="variable-name" wrapperClassName="prompt-input" value={name} placeholder="{table_header}" useCommonStyling onChange={handleNameChange} />
=======
										<SimpleInput id="variable-name" wrapperClassName="prompt-input" value={name} placeholder="{table_header}" useCommonStyling onChange={(text: string) => setName(text)} />
>>>>>>> 243bfb16 (create new prompt engineer page & fix conflicts)
									</div>
								</div>
								<div>
									<label className="inline-block text-sm font-medium mb-2" htmlFor="variable-display-name">Variable Label (Display Name)</label>
									<div className="prompt-input-container no-margin rounded-md">
<<<<<<< HEAD
										<SimpleInput id="variable-display-name" wrapperClassName="prompt-input" value={displayName} placeholder="Table Header" useCommonStyling onChange={handleDisplayNameChange} />
=======
										<SimpleInput id="variable-display-name" wrapperClassName="prompt-input" value={displayName} placeholder="Table Header" useCommonStyling onChange={(text: string) => setDisplayName(text)} />
>>>>>>> 243bfb16 (create new prompt engineer page & fix conflicts)
									</div>
								</div>
							</div>
							<div className="grid items-center gap-4 mb-4" style={{gridTemplateColumns: '1fr auto auto'}}>
								<div>
									<label className="inline-block text-sm font-medium mb-2" htmlFor="variable-type">Input Type</label>
									<div className="prompt-input-container no-margin rounded-md">
<<<<<<< HEAD
										<CommonSelect id="variable-type" defaultValue={type} options={variableTypes} onSelectedValueChange={handleTypeChange} />
=======
										<CommonSelect id="variable-type" defaultValue={type} options={variableTypes} onSelectedValueChange={(text: PromptInputVariableEngineerType) => setType(text)} />
>>>>>>> 243bfb16 (create new prompt engineer page & fix conflicts)
									</div>
								</div>
								<div>
									<label className="inline-block text-sm mb-2 text-[#4A5567]" htmlFor="variable-required">Required</label>
									<div className="prompt-input-container no-margin prompt-checkbox-container rounded-md">
<<<<<<< HEAD
										<CommonCheckbox checked={required} onChange={handleRequiredChange} />
									</div>
								</div>
								<div>
									<label className="inline-block text-sm mb-2 text-[#4A5567]" htmlFor="variable-json">JSON</label>
									<div className="prompt-input-container no-margin prompt-checkbox-container rounded-md">
										<CommonCheckbox checked={json} onChange={handleJsonChange} />
=======
										<SimpleInput id="variable-required" type="checkbox" wrapperClassName="prompt-input" value="" checked={required} useCommonStyling onChange={() => setRequired(!required)} />
									</div>
								</div>
								<div>
									<label className="inline-block text-sm mb-2" htmlFor="variable-json">JSON</label>
									<div className="prompt-input-container no-margin prompt-checkbox-container rounded-md">
										<SimpleInput id="variable-json" type="checkbox" wrapperClassName="prompt-input" value="" checked={json} useCommonStyling onChange={() => setJson(!json)} />
>>>>>>> 243bfb16 (create new prompt engineer page & fix conflicts)
									</div>
								</div>
							</div>
							<div>
								<label className="inline-block text-sm font-medium mb-2" htmlFor="variable-define-variable">Define Variable</label>
<<<<<<< HEAD
								{type === "String" && (
									<div className="prompt-input-container prompt-textarea-container no-margin">
										<SimpleTextarea wrapperClassName="prompt-input" value={definition} placeholder="{header / Customer / Product /Quantity / Invoice Amount}" useCommonStyling onChange={handleDefinitionChange}></SimpleTextarea>
									</div>
								)}
								{type === "Array of Strings" && (
									<div className="prompt-input-container prompt-multi-tag-container no-margin rounded-md">
										<PromptMultiTagInputs values={values} onChange={setValues}/>
									</div>
								)}
=======
								<div className="prompt-input-container prompt-textarea-container no-margin">
									<SimpleTextarea wrapperClassName="prompt-input" value={definition} placeholder="{header / Customer / Product /Quantity / Invoice Amount}" useCommonStyling onChange={(text: string) => setDefinition(text)}></SimpleTextarea>
								</div>
>>>>>>> 243bfb16 (create new prompt engineer page & fix conflicts)
							</div>
						</div>
					</div>
				</div>
			</div>
		)}
	</>

  )
}
export default PromptInputVariableEngineer