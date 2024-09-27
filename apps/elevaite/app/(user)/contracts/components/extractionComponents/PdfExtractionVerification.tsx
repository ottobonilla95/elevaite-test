import { CommonButton, CommonInput, ElevaiteIcons } from "@repo/ui/components";
import { useEffect, useState } from "react";
import { isObject } from "../../../../lib/actions/generalDiscriminators";
import { useContracts } from "../../../../lib/contexts/ContractsContext";
import { CONTRACT_STATUS, CONTRACT_TYPES, type ContractObjectVerification, type ContractObjectVerificationItem } from "../../../../lib/interfaces";
import "./PdfExtractionVerification.scss";
import { VerificationLineItems } from "./VerificationLineItems";




export function PdfExtractionVerification(): JSX.Element {
    const contractsContext = useContracts();
    const [verificationData, setVerificationData] = useState<ContractObjectVerification>();
    const [isLineItemsFullScreen, setIsLineItemsFullScreen] = useState(false);

    
    useEffect(() => {
        setVerificationData(contractsContext.selectedContract?.verification);
    }, [contractsContext.selectedContract]);



    return (
        <div className="pdf-extraction-verification-container">

            {contractsContext.selectedContract?.status === CONTRACT_STATUS.PROCESSING ? 
                <div className="no-verification">
                    <ElevaiteIcons.SVGSpinner/><span>Verification in progress...</span>
                </div>
            : !verificationData || (!verificationData.po && !verificationData.invoice.length && !verificationData.vsow.length) ?
                    <div className="no-verification">
                        There is no verification data for this document.
                    </div>
                :
                <>                    
                    {contractsContext.selectedContract?.content_type === CONTRACT_TYPES.PURCHASE_ORDER ? undefined :
                        <div className="pdf-verification-block">
                            <div className="pdf-verification-label">
                                Purchase Order Information
                            </div>
                            {!verificationData.po ? 
                                <div className="no-info">
                                    No verification information.
                                </div>
                            :
                                <>
                                    <VerificationBit data={verificationData.po} valueKey="po_number" label="PO Number" />
                                    <VerificationBit data={verificationData.po} valueKey="supplier" label="Supplier" />
                                    <VerificationBit data={verificationData.po} valueKey="total_amount" label="Total Amount" />
                                </>
                            }
                        </div>
                    }
                    <div className="pdf-verification-block table">
                        <div className="pdf-verification-label expanded">
                            <span>Line Items</span>                            
                            {(!contractsContext.selectedContract?.line_items) || contractsContext.selectedContract.line_items.length === 0 ? undefined :
                                <CommonButton
                                    onClick={() => { setIsLineItemsFullScreen(true); }}
                                    noBackground
                                >
                                    <ElevaiteIcons.SVGZoom/>
                                </CommonButton>
                            }
                        </div>
                        {(!contractsContext.selectedContract?.line_items) || contractsContext.selectedContract.line_items.length === 0 ? 
                            <div className="no-info">
                                No line items.
                            </div>
                        :
                            <VerificationLineItems
                                lineItems={contractsContext.selectedContract.line_items}
                                fullScreen={isLineItemsFullScreen}
                                onFullScreenClose={() => { setIsLineItemsFullScreen(false); }}
                            />
                        }
                    </div>
                    {verificationData.vsow.length === 0 ? undefined
                    :
                        <div className="pdf-verification-block">
                            <div className="pdf-verification-label">
                                VSOW
                            </div>
                            {verificationData.vsow.map((vsow, index) => 
                                <div className="fragment" key={`${vsow.file_id?.toString() ?? ""}_vsow_${index.toString()}`}>
                                    <VerificationBit data={vsow} valueKey="po_number" label="PO Number" />
                                    <VerificationBit data={vsow} valueKey="supplier" label="Supplier" />
                                    <VerificationBit data={vsow} valueKey="total_amount" label="Total Amount" />
                                </div>
                            )}
                        </div>
                    }
                    {verificationData.invoice.length === 0 ? undefined
                    :
                        <div className="pdf-verification-block">
                            <div className="pdf-verification-label">
                                Invoices
                            </div>
                            {verificationData.invoice.map((invoice, index) => 
                                <div className="fragment" key={`${invoice.file_id?.toString() ?? ""}_invoice_${index.toString()}`}>
                                    <VerificationBit data={invoice} valueKey="po_number" label="PO Number" />
                                    <VerificationBit data={invoice} valueKey="supplier" label="Supplier" />
                                    <VerificationBit data={invoice} valueKey="total_amount" label="Total Amount" />
                                </div>
                            )}
                        </div> 
                    }
                    {contractsContext.selectedContract?.content_type !== CONTRACT_TYPES.INVOICE ? undefined :
                        <div className="pdf-verification-block">
                            <div className="pdf-verification-label">
                                Comments
                            </div>
                            {!contractsContext.selectedContract.response_comments ? 
                                <div className="no-info">
                                    No Comments for this invoice.
                                </div>
                            :
                                <div className="verification-comments">
                                    {contractsContext.selectedContract.response_comments.map(comment => 
                                        <div key={comment}>{comment}</div>
                                    )}
                                </div>
                            }
                        </div> 
                    }

                </>
            }


        </div>
    );
}






interface VerificationBitProps {
    data: ContractObjectVerificationItem;
    valueKey: keyof ContractObjectVerificationItem;
    label: string;
}

function VerificationBit(props: VerificationBitProps): React.ReactNode {
    const [value, setValue] = useState<string>();
    const [isVerified, setIsVerified] = useState<boolean>();

    useEffect(() => {
        const item = props.data[props.valueKey];
        if (isObject(item)) {
            setValue(item.value);
            setIsVerified(item.verification_status);
        }
    }, [props.data, props.valueKey]);

    return (
        !value || typeof value !== "string" ? undefined :
        <CommonInput
            label={props.label}
            initialValue={value}
            disabled
            noDisabledTooltip
            labelIcon={isVerified ? 
                <div className="verification-icon success"><ElevaiteIcons.SVGCheckmark/></div> :
                <div className="verification-icon failure"><ElevaiteIcons.SVGXmark/></div>
            }
        />
    );
}


