import React, { useState, useRef, useEffect } from "react";

interface PromptMultiTagInputsProps {
  placeholder?: string;
  values?: string[];
  onChange?: (values: string[]) => void;
  disabled?: boolean;
}

function PromptMultiTagInputs({ placeholder, values, onChange, disabled }: PromptMultiTagInputsProps): JSX.Element {
  const [inputs, setInputs] = useState<string[]>(values ?? []);
  const [inputValue, setInputValue] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    setInputs(values ?? []);
  }, [values]);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setInputValue(e.target.value);
  };

  const addInput = (val: string) => {
    const trimmed = val.trim();
    if (trimmed && !inputs.includes(trimmed)) {
      const newInputs = [...inputs, trimmed];
      setInputs(newInputs);
      setInputValue("");
      onChange?.(newInputs);
    }
  };

  const handleInputKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (
      (e.key === "Enter" || e.key === "," || e.key === "Tab") &&
      inputValue.trim() !== ""
    ) {
      e.preventDefault();
      addInput(inputValue);
    } else if (e.key === "Backspace" && inputValue === "" && inputs.length > 0) {
      removeInput(inputs.length - 1);
    }
  };

  const removeInput = (index: number) => {
    const newInputs = inputs.filter((item, i) => i !== index);
    setInputs(newInputs);
    onChange?.(newInputs);
    setTimeout(() => inputRef.current?.focus(), 0);
  };

  return (
    <div className="prompt-multi-tag-inputs p-4">
      <div className="inner flex flex-wrap items-start gap-2 border rounded-lg p-4 min-h-[40px] bg-white overflow-auto">
        {inputs.map((item, index) => (
          <span
            key={item}
            className="tag flex items-center bg-gray-200 rounded px-2 py-1 text-sm"
          >
            {item}
            <button
              type="button"
              className="ml-1 text-gray-500 hover:text-red-500"
              onClick={() => { removeInput(index); }}
              aria-label="Remove"
            >
              &times;
            </button>
          </span>
        ))}
        <input
          ref={inputRef}
          className="flex-1 min-w-[80px] border-none outline-none bg-transparent text-sm"
          type="text"
          value={inputValue}
          onChange={handleInputChange}
          onKeyDown={handleInputKeyDown}
          placeholder={inputs.length === 0 ? placeholder : ""}
          disabled={disabled}
        />
      </div>
    </div>
  );
}

export default PromptMultiTagInputs;