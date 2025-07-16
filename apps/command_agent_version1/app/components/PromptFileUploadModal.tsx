import { CommonModal } from '@repo/ui/components';
import React, { useRef } from 'react';
import { FileUploader } from "react-drag-drop-files";
import { toast } from 'react-toastify';
import { LoadingKeys, usePrompt } from '../ui/contexts/PromptContext';
import { PromptInputTypes } from '../lib/interfaces';
import PromptLoading from './PromptLoading';



function PromptToast({ data }: { data: { num_pages: number } }): React.ReactElement {
  return <div className="prompt-toast rounded-md font-bold text-sm flex items-center justify-between w-full">
		PDF loaded successfully. Total {data.num_pages} {data.num_pages > 1 ? 'pages' : 'page'} extracted.
	</div>
}

function PromptFileUploadModal() {
	const fileTypes = ["PDF", "JPG", "PNG"];
	const promptsContext = usePrompt();

	const handleChange = (newFile: File | File[] | FileList): void => {
		let file: File | undefined;

		if (newFile instanceof File) {
			file = newFile;
		} else if (Array.isArray(newFile)) {
			file = newFile[0];
		} else if (typeof newFile === "object" && "length" in newFile) {
			file = newFile[0];
		}

		if (!(file instanceof File)) {
			return;
		}

		promptsContext.setFile(file);
	};

	let isImage = false;

	const handleUpload = async (e: React.MouseEvent<HTMLButtonElement>) => {
		e.preventDefault();

		if (promptsContext.file && promptsContext.file.type !== "application/pdf") {
			isImage = true;
		}

		const data = await promptsContext.fileUpload(true, promptsContext.file as File, isImage);
		const finalData = await promptsContext.processCurrentPage();
		console.log("File uploaded:", data);
		console.log("Processed Current Page:", finalData);

		if (data && finalData) {
			//promptsContext.setTestingConsoleActiveClass('half-expanded');
			promptsContext.setInvoiceImage(data.image as string);
			promptsContext.setInvoiceNumPages(data.num_pages as number);
			promptsContext.setShowFileUploadModal(false);
/* 			promptsContext.setPromptInputs(
				promptsContext.defaultPromptInputs.map(input => {
					console.log(input)
					if (input.type === PromptInputTypes.DocumentHeader) {
						return {
							...input,
							values: finalData.document_headers,
							//id: crypto.randomUUID().toString(),
						}
					} else if (input.type === PromptInputTypes.LineItemHeader) {
						return {
							...input,
							values: finalData.line_item_headers,
							//id: crypto.randomUUID().toString(),
						}
					}					
					return input;
					
				})
			); */

			promptsContext.setCurrentPage(1);
			toast.success(
				PromptToast,
				{
					position: 'bottom-right',
					//autoClose: false,
					data: {
						num_pages: data.num_pages || 0,
					}
				}
			)
		}
	}

	const hiddenFileInput = useRef<HTMLInputElement | null>(null);

	return (
		<CommonModal className="file-upload-modal">
			<div className="relative">
				{Boolean(promptsContext.loading[LoadingKeys.Uploading]) && (
					<div className="absolute inset-0 z-50 flex items-center justify-center bg-[#F8FAFC]/80 rounded-lg">
						<PromptLoading />
					</div>
				)}

				<form className="bg-white p-5 rounded-lg w-[600px]">
					<div className="mb-5 flex items-center justify-between">
						<h2 className="text-lg font-medium">File Upload</h2>
						<button onClick={() => { promptsContext.setShowFileUploadModal(false); }} type='button'>
							<svg width="12" height="13" viewBox="0 0 12 13" fill="none" xmlns="http://www.w3.org/2000/svg">
								<path d="M11 1.5L1 11.5M1 1.5L11 11.5" stroke="#97A3B6" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
							</svg>
						</button>
					</div>
					<div className="rounded-md p-5" style={{ border: '1px solid #E3E8EF' }}>
						<FileUploader
							multiple
							handleChange={handleChange}
							name="file"
							types={fileTypes}
						>
							<Dropzone />
						</FileUploader>
					</div>

					{promptsContext.file instanceof File && (
						<div className="my-5 rounded-md p-3 flex items-center justify-between" style={{ border: '1px solid #E3E8EF' }}>
							<div className="flex items-center gap-2">
								<svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
									<path d="M10.0391 0.833985C10.4506 0.853451 10.8124 1.21547 10.832 1.62695C10.833 1.6468 10.833 1.65779 10.833 1.67969V5.36035C10.833 5.57041 10.8335 5.77495 10.8477 5.94824C10.8632 6.13866 10.8995 6.36375 11.0146 6.58984C11.1744 6.9034 11.4296 7.15857 11.7432 7.31836C11.9693 7.4336 12.1943 7.47076 12.3848 7.48633C12.5582 7.5005 12.7633 7.50003 12.9736 7.5H16.6533C16.6751 7.5 16.6864 7.50005 16.7061 7.50098C17.1175 7.52061 17.4795 7.88245 17.499 8.29395C17.5 8.31365 17.5 8.32025 17.5 8.33301V14.3682C17.5 15.0387 17.4997 15.5921 17.4629 16.043C17.4246 16.5114 17.3428 16.9422 17.1367 17.3467C16.8171 17.9739 16.3069 18.4841 15.6797 18.8037C15.2755 19.0096 14.8451 19.0916 14.377 19.1299C13.926 19.1667 13.3719 19.167 12.7012 19.167H7.29883C6.62806 19.167 6.07402 19.1667 5.62305 19.1299C5.15494 19.0916 4.72453 19.0096 4.32031 18.8037C3.69311 18.4841 3.18286 17.9739 2.86328 17.3467C2.65721 16.9422 2.57538 16.5114 2.53711 16.043C2.50029 15.5921 2.49999 15.0387 2.5 14.3682V5.63184C2.49999 4.96132 2.50029 4.4079 2.53711 3.95703C2.57538 3.48862 2.65721 3.05777 2.86328 2.65332C3.18286 2.02612 3.69311 1.51586 4.32031 1.19629C4.72453 0.990413 5.15494 0.908392 5.62305 0.870117C6.07402 0.833271 6.62806 0.832998 7.29883 0.833008H10C10.0129 0.833003 10.0195 0.833061 10.0391 0.833985ZM6.66699 14.167C6.20675 14.167 5.83301 14.5398 5.83301 15C5.83301 15.4602 6.20676 15.833 6.66699 15.833H13.333C13.7932 15.833 14.167 15.4602 14.167 15C14.167 14.5398 13.7932 14.167 13.333 14.167H6.66699ZM6.66699 10.833C6.20675 10.833 5.83301 11.2068 5.83301 11.667C5.83318 12.1271 6.20686 12.5 6.66699 12.5H13.333C13.7931 12.5 14.1668 12.1271 14.167 11.667C14.167 11.2068 13.7932 10.833 13.333 10.833H6.66699ZM6.66699 7.5C6.20686 7.5 5.83318 7.87292 5.83301 8.33301C5.83301 8.79325 6.20675 9.16699 6.66699 9.16699H8.33301C8.79325 9.16699 9.16699 8.79325 9.16699 8.33301C9.16682 7.87292 8.79314 7.5 8.33301 7.5H6.66699ZM13.0137 1.92188C13.1279 1.94933 13.208 2.02916 13.3672 2.18848L16.1445 4.96582C16.3041 5.12521 16.3837 5.20505 16.4111 5.31934C16.4499 5.48075 16.3652 5.68472 16.2236 5.77148C16.1234 5.83291 16.0014 5.83301 15.7568 5.83301H13.167C12.9337 5.833 12.8167 5.83344 12.7275 5.78809C12.6491 5.74814 12.5858 5.68387 12.5459 5.60547C12.5005 5.51639 12.5 5.40005 12.5 5.16699V2.57715C12.5 2.33246 12.5001 2.2096 12.5615 2.10938C12.6483 1.96801 12.8524 1.88332 13.0137 1.92188Z" fill="#97A3B6" />
								</svg>
								<div className="text-xs font-medium">{promptsContext.file.name}</div>
								<div className="w-[3px] h-[3px] rounded-full" style={{ background: '#CDD5E0' }}/>
								<div className="text-gray-500 text-xs font-medium">
									{typeof promptsContext.file.size === "number"
										? (promptsContext.file.size / (1024 * 1024)).toFixed(2) + "MB"
										: "Unknown size"
										}
								</div>
							</div>
							<button>
								<svg width="18" height="18" viewBox="0 0 18 18" fill="none" xmlns="http://www.w3.org/2000/svg">
									<path d="M6.5 1.5H11.5M1.5 4H16.5M14.8333 4L14.2489 12.7661C14.1612 14.0813 14.1174 14.7389 13.8333 15.2375C13.5833 15.6765 13.206 16.0294 12.7514 16.2497C12.235 16.5 11.5759 16.5 10.2578 16.5H7.74221C6.42409 16.5 5.76503 16.5 5.24861 16.2497C4.79396 16.0294 4.41674 15.6765 4.16665 15.2375C3.88259 14.7389 3.83875 14.0813 3.75107 12.7661L3.16667 4M7.33333 7.75V11.9167M10.6667 7.75V11.9167" stroke="#DF1C41" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
								</svg>
							</button>
						</div>
					)}

					{/* {promptsContext.invoiceImage && (
					<img src={`data:content/type;base64,${promptsContext.invoiceImage}`} alt="" />
				)} */}

					<input type="file" name="my-file" ref={hiddenFileInput} className="absolute" style={{ left: '-999px' }} />
					<div className="flex justify-end gap-2 mt-5">
						<button className="btn btn-outline" onClick={() => promptsContext.setShowFileUploadModal(false)}>Back</button>
						<button className="btn btn-primary" onClick={handleUpload}>Attach</button>
					</div>
				</form>
			</div>
		</CommonModal>
	)
}
export default PromptFileUploadModal

export function Dropzone(): React.ReactElement {
	return (
		<div className="p-7 rounded-md text-center" style={{ border: '1px dashed #CDD5E0', background: '#F8FAFC' }}>
			<div className="flex justify-center mb-2">
				<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
					<path fillRule="evenodd" clipRule="evenodd" d="M19.4914 8.18681C22.0836 8.84987 24 11.2011 24 14C24 17.3137 21.3137 20 18 20H6.5C2.91015 20 0 17.0899 0 13.5C0 10.4377 2.11764 7.87004 4.96841 7.18148C6.32398 4.69055 8.96456 3 12 3C15.4283 3 18.3528 5.15641 19.4914 8.18681ZM7.29289 12.7071C7.68342 13.0976 8.31658 13.0976 8.70711 12.7071L11 10.4142L11 16C11 16.5523 11.4477 17 12 17C12.5523 17 13 16.5523 13 16L13 10.4142L15.2929 12.7071C15.6834 13.0976 16.3166 13.0976 16.7071 12.7071C17.0976 12.3166 17.0976 11.6834 16.7071 11.2929L12.7071 7.29289C12.3166 6.90237 11.6834 6.90237 11.2929 7.29289L7.29289 11.2929C6.90237 11.6834 6.90237 12.3166 7.29289 12.7071Z" fill="#FF681F" />
				</svg>
			</div>
			<div className="font-medium text-sm mb-2">Click to Upload, or Drop your PDF here.</div>
			{/* <div className="text-gray-500 text-xs">Compatible file formats are PDF</div>
		<div className="text-gray-500 text-xs">Upload up to five files.</div> */}
		</div>
	)
}