import { CommonButton, ElevaiteIcons } from "@repo/ui/components";
import "./ModelsHeader.scss";



interface ModelsHeaderProps {

}

export function ModelsHeader(props: ModelsHeaderProps): JSX.Element {


    function handleOpenArchive():void {
        console.log("Opening archive");
    }

    return (
        <div className="models-header-container">

            <div className="part-container left">
                <CommonButton
                    className="archive-button"
                    onClick={handleOpenArchive}
                >
                    <ElevaiteIcons.SVGArchive/>
                    Open Archive
                </CommonButton>
            </div>

            <div className="part-container right">
                <CommonButton
                    className="icon-button"
                    noBackground
                >
                    <ElevaiteIcons.SVGDownload/>
                </CommonButton>
                <CommonButton
                    className="icon-button play"
                    noBackground
                >
                    <ElevaiteIcons.SVGPlay/>
                </CommonButton>
            </div>

        </div>
    );
}