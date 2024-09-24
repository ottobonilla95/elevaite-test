import { CommonInput, ElevaiteIcons } from "@repo/ui/components";
import { useEffect, useState } from "react";
import { isObject } from "../../../../lib/actions/generalDiscriminators";
import { useContracts } from "../../../../lib/contexts/ContractsContext";
import { type ContractExtractionDictionary, type ContractObjectVerification, type ContractObjectVerificationItem } from "../../../../lib/interfaces";
import { ExtractedTableBit } from "./ExtractedTableBit";
import "./PdfExtractionVerification.scss";




export function PdfExtractionVerification(): JSX.Element {
    const contractsContext = useContracts();
    const [verificationData, setVerificationData] = useState<ContractObjectVerification>();
    const [lineItems, setLineItems] = useState<Record<string, string>[]>([]);

    
    useEffect(() => {
        setVerificationData(contractsContext.selectedContract?.verification);
        if (contractsContext.selectedContract?.response)
            setLineItems(getLineItems(contractsContext.selectedContract.response));
    }, [contractsContext.selectedContract]);




    function getLineItems(extractedData: ContractExtractionDictionary): Record<string, string>[] {
        const items: Record<string, string>[] = [];
      
        Object.values(extractedData).forEach(page => {            
            Object.values(page).forEach(value => {
                if (typeof value !== 'string') {
                    items.push(value);
                }
            });
        });
      
        return items;
      }





    return (
        <div className="pdf-extraction-verification-container">

            {!verificationData ? 
                    <div className="no-verification">
                        There is no verification data for this document.
                    </div>
                :
                <>                    
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
                    <div className="pdf-verification-block table">
                        <div className="pdf-verification-label">
                            Line Items
                        </div>
                        {lineItems.length === 0 ? 
                            <div className="no-info">
                                No line items.
                            </div>
                        :
                            <ExtractedTableBit
                                label="Line Items"
                                data={lineItems}
                                hideLabel
                            />
                        }
                    </div>
                    <div className="pdf-verification-block">
                        <div className="pdf-verification-label">
                            Contracts
                        </div>
                        {verificationData.vsow.length === 0 ? 
                            <div className="no-info">
                                No contract information.
                            </div>
                        :
                            verificationData.vsow.map((vsow, index) => 
                                <div className="fragment" key={`${vsow.file_id?.toString() ?? ""}_vsow_${index.toString()}`}>
                                    <VerificationBit data={vsow} valueKey="po_number" label="PO Number" />
                                    <VerificationBit data={vsow} valueKey="supplier" label="Supplier" />
                                    <VerificationBit data={vsow} valueKey="total_amount" label="Total Amount" />
                                </div>
                            )
                        }
                    </div>
                    <div className="pdf-verification-block">
                        <div className="pdf-verification-label">
                            Invoices
                        </div>
                        {verificationData.invoice.length === 0 ? 
                            <div className="no-info">
                                No invoice information.
                            </div>
                        :
                            verificationData.invoice.map((invoice, index) => 
                                <div className="fragment" key={`${invoice.file_id?.toString() ?? ""}_invoice_${index.toString()}`}>
                                    <VerificationBit data={invoice} valueKey="po_number" label="PO Number" />
                                    <VerificationBit data={invoice} valueKey="supplier" label="Supplier" />
                                    <VerificationBit data={invoice} valueKey="total_amount" label="Total Amount" />
                                </div>
                            )
                        }
                    </div>                

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


