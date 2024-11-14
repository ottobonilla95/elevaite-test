import { CommonButton, CommonInput, ElevaiteIcons } from "@repo/ui/components";
import React, { useEffect, useState } from "react";
import { VerificationLineItems } from "./VerificationLineItems";
import {
  CONTRACT_TYPES,
  type LoadingListObject,
  type ContractObject,
  type ContractObjectVerification,
  type ContractObjectVerificationItem,
  ContractStatus,
} from "@/interfaces";
import "./PdfExtractionVerification.scss";
import { isObject } from "@/actions/generalDiscriminators";

interface PdfExtractionVerificationProps {
  loading: LoadingListObject;
  selectedContract?: ContractObject;
}

export function PdfExtractionVerification(
  props: PdfExtractionVerificationProps
): JSX.Element {
  const [verificationData, setVerificationData] =
    useState<ContractObjectVerification | null>();
  const [supplier, setSupplier] = useState<string | undefined>();
  const [isLineItemsFullScreen, setIsLineItemsFullScreen] = useState(false);

  useEffect(() => {
    setVerificationData(props.selectedContract?.verification);
    setSupplier(
      props.selectedContract?.highlight?.supplier
        ? props.selectedContract.highlight.supplier
        : undefined
    );
  }, [props.selectedContract]);

  function getFormattedComments(comments: string[]): React.ReactElement[] {
    const commentCount = comments.reduce<Record<string, number>>(
      (acc, comment) => {
        acc[comment] = (acc[comment] || 0) + 1;
        return acc;
      },
      {}
    );

    return Object.keys(commentCount).map((comment) => (
      <div key={comment}>
        {comment} {commentCount[comment] > 1 && `(x${commentCount[comment]})`}
      </div>
    ));
  }

  return (
    <div className="pdf-extraction-verification-container">
      {props.selectedContract?.status === ContractStatus.Extracting ? (
        <div className="no-verification">
          <ElevaiteIcons.SVGSpinner />
          <span>Verification in progress...</span>
        </div>
      ) : !verificationData ||
        (!verificationData.po?.length &&
          !verificationData.invoice?.length &&
          !verificationData.vsow?.length &&
          !verificationData.csow?.length) ? (
        <div className="no-verification">
          There is no verification data for this document.
        </div>
      ) : (
        <>
          {props.selectedContract?.content_type ===
          CONTRACT_TYPES.PURCHASE_ORDER ? undefined : (
            <div className="pdf-verification-block">
              <div className="pdf-verification-label">
                Purchase Order Information
              </div>
              {!verificationData.po || verificationData.po.length === 0 ? (
                <div className="no-info">No verification information.</div>
              ) : (
                verificationData.po.map((po, index) => (
                  <div
                    className="fragment"
                    key={`${po.file_id?.toString() ?? ""}_po_${index.toString()}`}
                  >
                    <VerificationBit
                      data={po}
                      valueKey="po_number"
                      label="PO Number"
                    />
                    <VerificationBit
                      data={po}
                      valueKey="supplier"
                      label="Supplier"
                    />
                    {/* <VerificationBit data={po} valueKey="supplier" label="Supplier" overrideValue={supplier} /> */}
                    <VerificationBit
                      data={po}
                      valueKey="total_amount"
                      label="Total Amount"
                    />
                  </div>
                ))
              )}
            </div>
          )}
          <div className="pdf-verification-block table">
            <div className="pdf-verification-label expanded">
              <span>Line Items</span>
              {!props.selectedContract?.line_items ||
              props.selectedContract.line_items.length === 0 ? undefined : (
                <CommonButton
                  onClick={() => {
                    setIsLineItemsFullScreen(true);
                  }}
                  noBackground
                >
                  <ElevaiteIcons.SVGZoom />
                </CommonButton>
              )}
            </div>
            {!props.selectedContract?.line_items ||
            props.selectedContract.line_items.length === 0 ? (
              <div className="no-info">No line items.</div>
            ) : (
              <VerificationLineItems
                loading={props.loading}
                lineItems={props.selectedContract.line_items}
                fullScreen={isLineItemsFullScreen}
                onFullScreenClose={() => {
                  setIsLineItemsFullScreen(false);
                }}
              />
            )}
          </div>
          {verificationData.vsow?.length === 0 ? undefined : (
            <div className="pdf-verification-block">
              <div className="pdf-verification-label">VSOW</div>
              {verificationData.vsow?.map((vsow, index) => (
                <div
                  className="fragment"
                  key={`${vsow.file_id?.toString() ?? ""}_vsow_${index.toString()}`}
                >
                  <VerificationBit
                    data={vsow}
                    valueKey="po_number"
                    label="PO Number"
                  />
                  <VerificationBit
                    data={vsow}
                    valueKey="supplier"
                    label="Supplier"
                  />
                  {/* <VerificationBit data={vsow} valueKey="supplier" label="Supplier" overrideValue={supplier} /> */}
                  <VerificationBit
                    data={vsow}
                    valueKey="total_amount"
                    label="Total Amount"
                  />
                </div>
              ))}
            </div>
          )}
          {verificationData.csow?.length === 0 ? undefined : (
            <div className="pdf-verification-block">
              <div className="pdf-verification-label">CSOW</div>
              {verificationData.csow?.map((csow, index) => (
                <div
                  className="fragment"
                  key={`${csow.file_id?.toString() ?? ""}_csow_${index.toString()}`}
                >
                  <VerificationBit
                    data={csow}
                    valueKey="po_number"
                    label="PO Number"
                  />
                  <VerificationBit
                    data={csow}
                    valueKey="supplier"
                    label="Supplier"
                  />
                  {/* <VerificationBit data={csow} valueKey="supplier" label="Supplier" overrideValue={supplier} /> */}
                  <VerificationBit
                    data={csow}
                    valueKey="total_amount"
                    label="Total Amount"
                  />
                </div>
              ))}
            </div>
          )}
          {verificationData.invoice?.length === 0 ? undefined : (
            <div className="pdf-verification-block">
              <div className="pdf-verification-label">Invoices</div>
              {verificationData.invoice?.map((invoice, index) => (
                <div
                  className="fragment"
                  key={`${invoice.file_id?.toString() ?? ""}_invoice_${index.toString()}`}
                >
                  <VerificationBit
                    data={invoice}
                    valueKey="po_number"
                    label="PO Number"
                  />
                  <VerificationBit
                    data={invoice}
                    valueKey="supplier"
                    label="Supplier"
                    overrideValue={supplier}
                  />
                  <VerificationBit
                    data={invoice}
                    valueKey="total_amount"
                    label="Total Amount"
                  />
                </div>
              ))}
            </div>
          )}
          {!props.selectedContract?.response_comments ? undefined : (
            <div className="pdf-verification-block">
              <div className="pdf-verification-label">Comments</div>
              {props.selectedContract.response_comments.length === 0 ? (
                <div className="no-info">No Comments for this file.</div>
              ) : (
                <div className="verification-comments">
                  {getFormattedComments(
                    props.selectedContract.response_comments
                  )}
                </div>
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
}

interface VerificationBitProps {
  data: ContractObjectVerificationItem;
  valueKey: keyof ContractObjectVerificationItem;
  overrideValue?: string;
  label: string;
}

function VerificationBit(props: VerificationBitProps): React.ReactNode {
  const [value, setValue] = useState<string>();
  const [isVerified, setIsVerified] = useState<boolean>();

  useEffect(() => {
    const item = props.data[props.valueKey];
    if (isObject(item)) {
      setValue(props.overrideValue ?? item.value);
      setIsVerified(item.verification_status);
    }
  }, [props.data, props.valueKey, props.overrideValue]);

  return !value || typeof value !== "string" ? undefined : (
    <CommonInput
      label={props.label}
      initialValue={value}
      disabled
      noDisabledTooltip
      labelIcon={
        isVerified ? (
          <div className="verification-icon success">
            <ElevaiteIcons.SVGCheckmark />
          </div>
        ) : (
          <div className="verification-icon failure">
            <ElevaiteIcons.SVGXmark />
          </div>
        )
      }
    />
  );
}
