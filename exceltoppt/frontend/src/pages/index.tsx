import React from "react";
import { Frame10000047431 } from "@/icons/Frame10000047431";
import { Frame1000004748 } from "@/icons/Frame1000004748";
import { HelpCircle1 } from "@/icons/HelpCircle1";
import { LayersThree01 } from "@/icons/LayersThree01";
import { Play } from "@/icons/Play";
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
    return (
    <div className="workshop">
      <img className="frame" alt="Frame" src="/img/frame-1000004706.svg" />
      <div className="sidebar">
        <header className="header">
        <Frame1000004748 className="frame-1000004748" />
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
            <Play className="icon-instance-node" color="white" />
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
      <div className="title-wrapper">elevAIte - Applications</div>
      <div className="frame-5">
        <div className="overlap-group-wrapper">
          <div className="overlap-group-2">
            <div className="group">
              <img className="line" alt="Line" src="/img/line-848.svg" />
              <div className="ellipse-8" />
            </div>
            <div className="group-2">
              <img className="line-2" alt="Line" src="/img/line-849-1.svg" />
              <div className="ellipse-9" />
            </div>
            <div className="group-3">
              <img className="line-3" alt="Line" src="/img/line-849.svg" />
              <div className="ellipse-10" />
            </div>
          </div>
        </div>
        <div className="frame-6">
          <div className="frame-7">
            <div className="frame-8">
              <Frame10000047431 className="frame-9" />
              <div className="frame-10">
                <div className="frame-11">
                  <div className="text-wrapper-4">Support Bot</div>
                  <img className="solid" alt="Solid" src="/img/solid-1.svg" />
                </div>
                <div className="text-wrapper-5">By ElevAIte</div>
              </div>
            </div>
            <p className="p">
              Please feel free to ask me anything. I'll do my best to provide helpful answers.
            </p>
            <div className="frame-12">
              <button className="button-2"  onClick = {handleChatbot}>
                <div className="text-wrapper-6">Open</div>
              </button> 
            </div>
          </div>
          <div className="frame-7">
            <div className="frame-8">
              <div className="frame-9">
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
              <div className="frame-10">
                <div className="frame-11">
                  <div className="text-wrapper-4">AI Deck Builder</div>
                  <img className="solid" alt="Solid" src="/img/solid-1.svg" />
                </div>
                <div className="text-wrapper-5">By ElevAIte</div>
              </div>
            </div>
            <p className="p">
              Convert your spread sheets to presentations and ask questions.
            </p>
            <div className="frame-12">
              <button className="button-2" onClick = {handleAIDeckBuilder}>
                <div className="text-wrapper-6">Open</div>
              </button>
            </div>
          </div>
          <div className="frame-7">
            <div className="frame-8">
              <Server031 className="frame-9" />
              <div className="frame-10">
                <div className="frame-11">
                  <div className="text-wrapper-4">OPEXWISE Insights</div>
                  <img className="solid" alt="Solid" src="/img/solid-1.svg" />
                </div>
                <div className="text-wrapper-5">By ElevAIte</div>
              </div>
            </div>
            <p className="p">
              Your BI Application to make informed decisions. Data to insights.
            </p>
            <div className="frame-12">
              <button className="button-2">
                <div className="text-wrapper-6">Open</div>
              </button>
            </div>
          </div>
          <div className="frame-7">
            <div className="frame-8">
              <div className="material-symbols">
                <div className="overlap-group-4">
                  <div className="ellipse-13" />
                  <img className="vector-2" alt="Vector" src="/img/vector-1.svg" />
                  <img className="vector-3" alt="Vector" src="/img/vector.svg" />
                </div>
              </div>
              <div className="frame-10">
                <div className="frame-11">
                  <div className="text-wrapper-4">AI Campaign Builder</div>
                  <img className="solid" alt="Solid" src="/img/solid.svg" />
                </div>
                <div className="text-wrapper-5">By ElevAIte</div>
              </div>
            </div>
            <p className="p">
              Analyze attributes of past campaign metrics to build future campaigns.
            </p>
            <div className="frame-12">
              <button className="button-2">
                <div className="text-wrapper-6">Open</div>
              </button>
            </div>
          </div>
        </div>
      </div>
      <div className="copyright-wr">
        <p className="copyright">© Copyright 2023, All Rights Reserved by iOPEX Technologies</p>
      </div>
    </div>
  </div>
    );
};
