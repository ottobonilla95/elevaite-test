
import { ElevaiteIcons, CommonButton, Logos } from "@repo/ui/components";
import "./ApplicationDetails.scss";
import { ApplicationObject } from "../../../lib/interfaces";


export interface ApplicationDetailsProps {
    applicationDetails?: ApplicationObject;
    isLoading?: boolean;
    onBack?: () => void;
}


export default function ApplicationDetails({isLoading, applicationDetails, onBack}: ApplicationDetailsProps): JSX.Element {


    //TODO: Do this properly.
    function getIcon(id?: string): JSX.Element {
        if (!id) return <></>;
        if (id === "1") return <Logos.Aws/>;
        else return <Logos.Preprocess/>;
    }


    return (
        <div className="application-details-container">
            <div className="details-content">
                <CommonButton onClick={onBack} noBackground>
                    <ElevaiteIcons.SVGArrowBack/>
                </CommonButton>
                <div className="logo-container">
                    {isLoading ?
                        <ElevaiteIcons.SVGSpinner size={38} />
                        :
                        getIcon(applicationDetails?.id)
                    }                    
                </div>
                <div className="details-text-content">
                    {isLoading ? 
                        <div className="skeleton top"></div>
                        :
                        <div className="details-text-top">
                            <div className="details-name">{applicationDetails?.title}</div>
                            <div className="details-version">{applicationDetails?.version}</div>
                            {!applicationDetails?.creator ? null :
                                <div className="details-origin">
                                    <ElevaiteIcons.SVGDot/>
                                    {`By ${applicationDetails?.creator}`}
                                </div>
                            }
                        </div>
                    }
                    {isLoading ? 
                        <div className="skeleton bottom"></div>
                        :
                        <div className="details-text-bottom">
                            {applicationDetails?.description}
                        </div>
                    }
                </div>
            </div>
            
        </div>
    );
}