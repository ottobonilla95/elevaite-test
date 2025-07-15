import { CommonSelect, SimpleInput, SimpleTextarea } from "@repo/ui/components";
import { promptDataSetOptions, promptGroundTruthOptions, promptModelOptions, promptParameterOptions, promptStatusOption, promptTokenCostPricing, promptTypeOptions, promptVersionOption } from "../../../lib/mockup";
import "../../PromptInput.scss";
import PromptDetailActionButtons from "./PromptDetailActionButtons";

const PromptDetailEditingForm = () => {
  return (
	<div>
		<div className="p-4 rounded-xl" style={{ border: "1px solid #E2E8ED" }}>
			<div className="font-medium mb-4">Edit Prompt</div>
			<div className="prompt-form text-sm">
			<div className="mb-4">
				<label className="inline-block text-sm font-medium mb-2" htmlFor="prompt-name">Prompt Name</label>
				<div className="prompt-input-container no-margin rounded-md">
					<SimpleInput id="prompt-name" wrapperClassName="prompt-input" value="Data Analyzer" useCommonStyling onChange={() => console.log()} />
				</div>
			</div>
			<div className="mb-4">
				<label className="inline-block text-sm font-medium mb-2" htmlFor="prompt-type">Type</label>
				<div className="prompt-input-container prompt-select-container no-margin rounded-md">
					<CommonSelect id="prompt-type" defaultValue="Extract Data" options={promptTypeOptions} onSelectedValueChange={() => console.log()} />
				</div>
			</div>
			<div className="mb-4">
				<label className="inline-block text-sm font-medium mb-2" htmlFor="prompt-description">Description</label>
				<div className="prompt-input-container prompt-textarea-container no-margin">
					<SimpleTextarea id="prompt-description" wrapperClassName="prompt-input" value="Extracts information from invoices." placeholder="e.g. Extracts information from invoices" useCommonStyling onChange={() => console.log()}></SimpleTextarea>
				</div>
			</div>
			<div className="grid grid-cols-2 gap-4 mb-4">
				<div>
					<div className="prompt-input-container prompt-select-container no-margin rounded-md">
						<CommonSelect options={promptStatusOption} defaultValue="Ready" onSelectedValueChange={() => console.log()} />
					</div>
				</div>
				<div>
					<div className="prompt-input-container prompt-select-container no-margin rounded-md">
						<CommonSelect options={promptVersionOption} defaultValue="V2" onSelectedValueChange={() => console.log()} />
					</div>
				</div>
			</div>
			<hr className="my-4" />
			<div className="mb-4">
				<div className="prompt-input-container prompt-select-container no-margin rounded-md">
					<CommonSelect defaultValue="Parameters" options={promptParameterOptions} onSelectedValueChange={() => console.log()} />
				</div>
			</div>
			<div className="mb-4">
				<div className="prompt-input-container prompt-select-container no-margin rounded-md">
					<CommonSelect defaultValue="Data Set" options={promptDataSetOptions} onSelectedValueChange={() => console.log()} />
				</div>
			</div>
			<div className="mb-4">
				<div className="prompt-input-container prompt-select-container no-margin rounded-md">
					<CommonSelect defaultValue="Ground Truths" options={promptGroundTruthOptions} onSelectedValueChange={() => console.log()} />
				</div>
			</div>
			<div className="mb-4">
				<div className="prompt-input-container prompt-select-container no-margin rounded-md">
					<CommonSelect defaultValue="Token Cost & Pricing" options={promptTokenCostPricing} onSelectedValueChange={() => console.log()} />
				</div>
			</div>
			<div>
				<div className="prompt-input-container prompt-select-container no-margin rounded-md">
					<CommonSelect defaultValue="Models" options={promptModelOptions} onSelectedValueChange={() => console.log()} />
				</div>
			</div>
			</div>
		</div>
		<PromptDetailActionButtons />
	</div>
  )
}
export default PromptDetailEditingForm