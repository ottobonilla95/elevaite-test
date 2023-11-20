import React from "react";
import { Frame10000047431 } from "@/icons/Frame10000047431";
import { Frame1000004748 } from "@/icons/Frame1000004748";
import { HelpCircle1 } from "@/icons/HelpCircle1";
import { HelpCircle} from "@/icons/HelpCircle";
import { LayersThree01 } from "@/icons/LayersThree01";
import { Play } from "@/icons/Play";
import { Play1 } from "@/icons/Play1";
import { Server03 } from "@/icons/Server03";
import { Server031 } from "@/icons/Server031";
import { Settings02 } from "@/icons/Settings02";
import { useRouter } from 'next/router';

export default function Home() {

    const router = useRouter();
    const handleAIDeckBuilder = () =>{
      window.open("http://localhost:3000/homepage", "_blank");

    }
    const handleChatbot = () =>{
      window.open("https://elevaite-cb.iopex.ai", "_blank");

  }
  const handleOpexwise = () =>{
    window.open("https://arlo.opexwise.ai", "_blank");

}
    return (
      <div className="workshop">
       <div className="sidebar">
        <header className="header">
          <Frame1000004748 className="frame" />
        </header>
        <div className="div">
          <div className="button">
            <LayersThree01 className="icon-instance-node" color="white" />
          </div>
          <div className="button">
            <Settings02 className="icon-instance-node" color="white" />
          </div>
          <div className="button">
            <Server03 className="icon-instance-node" color="white" />
          </div>
          <div className="play-wrapper">
            <Play1 className="icon-instance-node" color="white" />
          </div>
          <div className="cil-applications-wrapper">
            <div className="icon-instance-node">
              <div className="overlap-group">
                <div className="ellipse" />
                <div className="ellipse-2" />
                <div className="ellipse-3" />
                <div className="ellipse-4" />
                <div className="ellipse-5" />
                <div className="ellipse-6" />
                <div className="ellipse-7" />
                <img className="vector" alt="Vector" src="/img/vector-2.svg" />
              </div>
            </div>
          </div>
        </div>
      </div>
      <div className="frame-2">
        <div className="heading">
          <div className="heading-wrapper">
            <div className="text-wrapper">Applications</div>
          </div>
          <div className="frame-3">
            <HelpCircle className="icon-instance-node" />
          </div>
        </div>
        <div className="frame-5">
          <img className="frame-6" alt="Frame" src="/img/frame-1000004706.svg" />
          <div className="overlap-group-wrapper">
            <div className="overlap-group-2">
              <div className="group">
                <img className="line" alt="Line" src="/img/line-849-1.png" />
                <div className="ellipse-8" />
              </div>
              <div className="group-2">
                <img className="line-2" alt="Line" src="/img/line-849-1.png" />
                <div className="ellipse-9" />
              </div>
              <div className="group-3">
                <img className="line" alt="Line" src="/img/line-849-1.png" />
                <div className="ellipse-10" />
              </div>
            </div>
          </div>
          <div className="frame-7">
          </div>
          <div className="frame-9">
            <div className="frame-10">
              <div className="frame-11">
                <div className="frame-12">
                  <img
                    className="expand-more"
                    alt="Expand more"
                    src="/img/expand-more-fill0-wght400-grad0-opsz48-1-1-2.svg"
                  />
                  <div className="text-wrapper-5">elevAIte for Support</div>
                </div>
                <img className="frame-13" alt="Frame" src="/img/frame-1000004627.svg" />
              </div>
              <div className="frame-wrapper" onClick={handleChatbot}>
                <div className="div-wrapper">
                  <div className="frame-14">
                    <div className="frame-15">
                      <Frame10000047431 className="frame-16" />
                      <div className="frame-17">
                        <div className="frame-18">
                          <div className="text-wrapper-6">Support Bot</div>
                          <img className="solid" alt="Solid" src="/img/solid-3.svg" />
                        </div>
                        <div className="text-wrapper-7">By elevAIte</div>
                      </div>
                      <div className="frame-19">
                        <div className="text-wrapper-8">Documentation</div>
                      </div>
                    </div>
                    <div className="frame-20">
                      <p className="text-wrapper-9">
                      Please feel free to ask me anything. I'll do my best to provide helpful answers.
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div className="frame-10">
              <div className="frame-21">
                <div className="frame-12">
                  <img
                    className="expand-more"
                    alt="Expand more"
                    src="/img/expand-more-fill0-wght400-grad0-opsz48-1-1-2.svg"
                  />
                  <div className="text-wrapper-5">elevAIte for Finance</div>
                </div>
                <img className="frame-13" alt="Frame" src="/img/frame-1000004627-2.svg" />
              </div>
              <div className="frame-wrapper" onClick={handleAIDeckBuilder}>
                <div className="frame-22">
                  <div className="frame-15">
                    <div className="frame-16">
                      <div className="overlap-group-3">
                        <div className="ellipse-11" />
                        <div className="ellipse-12" />
                        <img
                          className="vscode-icons-file"
                          alt="Vscode icons file"
                          src="/img/vscode-icons-file-type-excel.svg"
                        />
                        <img
                          className="vscode-icons-file-2"
                          alt="Vscode icons file"
                          src="/img/vscode-icons-file-type-powerpoint.svg"
                        />
                      </div>
                    </div>
                    <div className="frame-17">
                      <div className="frame-18">
                        <div className="text-wrapper-6">AI Deck Builder</div>
                        <img className="solid" alt="Solid" src="/img/solid-3.svg" />
                      </div>
                      <div className="text-wrapper-7">By elevAIte</div>
                    </div>
                    <div className="frame-19">
                      <div className="text-wrapper-8">Documentation</div>
                    </div>
                  </div>
                  <p className="text-wrapper-10">
                  Convert your spread sheets to presentations and ask questions.
                  </p>
                </div>
              </div>
            </div>
            <div className="frame-10">
              <div className="frame-21">
                <div className="frame-12">
                  <img
                    className="expand-more"
                    alt="Expand more"
                    src="/img/expand-more-fill0-wght400-grad0-opsz48-1-1-2.svg"
                  />
                  <div className="text-wrapper-5">elevAIte for Revenue</div>
                </div>
                <img className="frame-13" alt="Frame" src="/img/frame-1000004627-2.svg" />
              </div>
              <div className="frame-23">
                <div className="insights" onClick={handleOpexwise}>
                  <div className="frame-15">
                    <Server031 className="frame-16" />
                    <div className="frame-17">
                      <div className="frame-18">
                        <div className="text-wrapper-6">elevAIte Insights</div>
                        <img className="solid" alt="Solid" src="/img/solid-3.svg" />
                      </div>
                      <div className="text-wrapper-7">By elevAIte</div>
                    </div>
                    <div className="frame-19">
                      <div className="text-wrapper-8">Documentation</div>
                    </div>
                  </div>
                  <p className="text-wrapper-10">
                  Your BI Application to make informed decisions. Data to insights.
                  </p>
                </div>
                <div className="frame-22">
                  <div className="frame-15">
                    <div className="material-symbols">
                      <div className="overlap-group-4">
                        <div className="ellipse-13" />
                        <img className="vector-2" alt="Vector" src="/img/vector.svg" />
                        <img className="vector-3" alt="Vector" src="/img/vector-1.svg" />
                      </div>
                    </div>
                    <div className="frame-17">
                      <div className="frame-18">
                        <div className="text-wrapper-6">AI Campaign Builder</div>
                        <img className="solid" alt="Solid" src="/img/solid-3.svg" />
                      </div>
                      <div className="text-wrapper-7">By elevAIte</div>
                    </div>
                    <div className="frame-19">
                      <div className="text-wrapper-8">Documentation</div>
                    </div>
                  </div>
                  <p className="text-wrapper-10">
                  Analyze attributes of past campaign metrics to build successful future campaigns.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    );
};
