"use client";

import React from "react";
import Pill from "../../ui/Pill";
import { getModelProviders, getModels, OUTPUT_FORMATS, getAgentTypeDisplay } from "./configUtils";
import { type ConfigurationTabProps } from "./types";
import { AGENT_TYPE, type AgentType } from "../../../lib/interfaces";

function ConfigurationTab({
    agent,
    agentType,
    deploymentType,
    modelProvider,
    model,
    outputFormat,
    setDeploymentType,
    setModelProvider,
    setModel,
    setOutputFormat,
    disabledFields,
    setAgentType,
    tags = "",
    setTags,
}: ConfigurationTabProps): JSX.Element {

    // Current model providers based on selected deployment type
    const modelProviders = getModelProviders(deploymentType);

    // Current models based on selected deployment type and model provider
    const models = getModels(deploymentType, modelProvider);

    // Available agent types for dropdown
    const availableAgentTypes = Object.values(AGENT_TYPE);

    return (
        <div className="configuration-tab gap-6 p-2">

            {/* Agent Type - Full Width Row */}
            <div className="parameter-item">
                {disabledFields ? (
                    <div className="flex flex-col gap-1">
                        <span className="">Agent Type</span>
                        <Pill
                            text={getAgentTypeDisplay(agentType)}
                            textColor="#0950C3"
                            backgroundColor="#EBF2FE"
                            className="flex-shrink"
                        />
                    </div>
                ) : (
                    <label className="flex flex-col gap-2">Agent Type
                        <select
                            value={agentType}
                            onChange={(e) => { setAgentType?.(e.target.value as AgentType); }}
                            className="w-full px-2 py-3 rounded-md text-sm text-gray-900 border border-gray-300 bg-white"
                            disabled={disabledFields}
                        >
                            {availableAgentTypes.map((type) => (
                                <option key={type} value={type}>{getAgentTypeDisplay(type)}</option>
                            ))}
                        </select>
                    </label>
                )}
            </div>

            {/* Tags - Full Width Row */}
            <div className="parameter-item">
                {disabledFields ? (
                    <div className="flex flex-col gap-1">
                        <span className="parameter-label">Tags</span>
                        <div className="flex flex-wrap gap-2">
                            {agent.agent.system_prompt.tags?.map(tag => (
                                <Pill
                                    key={`badge-${tag}`}
                                    text={tag}
                                    textColor="#0950C3"
                                    backgroundColor="#EBF2FE"
                                />
                            ))}
                        </div>
                    </div>
                ) : (
                    <label className="flex flex-col gap-1">Tags
                        <input
                            type="text"
                            value={tags}
                            onChange={(e) => { setTags?.(e.target.value); }}
                            placeholder="Enter tags separated by commas"
                            className="border border-gray-300 rounded-md px-3 py-2 text-sm text-gray-700"
                            disabled={disabledFields}
                        />
                    </label>
                )}
            </div>

            {/* Parameters Grid - Two Per Row */}
            <span className="text-sm font-medium">Parameters</span>
            <div className="parameters-grid">

                <div className="parameter-item">
                    {disabledFields ? (
                        <div className="flex flex-col gap-1">
                            <span className="parameter-label">Model</span>
                            <Pill
                                text={model}
                                textColor="#6C8271"
                                backgroundColor="#6C82711F"
                                className="flex-shrink"
                            />
                        </div>
                    ) : (
                        <label className="parameter-label">Model
                            <select
                                value={model}
                                onChange={(e) => { setModel(e.target.value); }}
                                className="parameter-select"
                                disabled={disabledFields}
                            >
                                {models.map((_model) => (
                                    <option key={_model} value={_model}>{_model}</option>
                                ))}
                            </select>
                        </label>
                    )}
                </div>
                <div className="parameter-item">
                    {disabledFields ? (
                        <div className="flex flex-col gap-1">
                            <span className="parameter-label">Model Charge Type</span>
                            <Pill
                                text={deploymentType}
                                textColor="#6C8271"
                                backgroundColor="#6C82711F"
                                className="flex-shrink"
                            />
                        </div>
                    ) : (
                        <label className="parameter-label">Model Charge Type
                            <select
                                value={deploymentType}
                                onChange={(e) => { setDeploymentType(e.target.value); }}
                                className="parameter-select"
                                disabled={disabledFields}
                            >
                                {["Elevaite", "Enterprise", "Cloud"].map((type) => (
                                    <option key={type} value={type}>{type}</option>
                                ))}
                            </select>
                        </label>
                    )}
                </div>
                <div className="parameter-item">
                    {disabledFields ? (
                        <div className="flex flex-col gap-1">
                            <span className="parameter-label">Output Format</span>
                            <Pill
                                text={outputFormat}
                                textColor="#6C8271"
                                backgroundColor="#6C82711F"
                                className="flex-shrink"
                            />
                        </div>
                    ) : (
                        <label className="parameter-label">Output Format
                            <select
                                value={outputFormat}
                                onChange={(e) => { setOutputFormat(e.target.value); }}
                                className="parameter-select"
                                disabled={disabledFields}
                            >
                                {OUTPUT_FORMATS.map((format) => (
                                    <option key={format} value={format}>{format}</option>
                                ))}
                            </select>
                        </label>
                    )}
                </div>
            </div>
        </div>
    );
}

export default ConfigurationTab;
