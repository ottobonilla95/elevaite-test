import { useCallback, useMemo } from "react";
import { type ItemDetailsValue } from "../interfaces";
import { getItemDetailWithDefault } from "../utilities/config";
import { useConfigPanel } from "../contexts/ConfigPanelContext";


export function useNodeConfig<T extends ItemDetailsValue>(key: string, defaultValue: T, typeGuard?: (value: ItemDetailsValue) => value is T
): [T, (value: T) => void] {
	const { selectedNode, draft, updateDraft } = useConfigPanel();

	const value = useMemo((): T => {
		// Draft takes priority over original node value
		if (key in draft) {
			const draftValue = draft[key];
			if (typeGuard) {
				if (typeGuard(draftValue)) return draftValue;
			} else {
				return draftValue as T;
			}
		}
		return getItemDetailWithDefault(selectedNode, key, defaultValue, typeGuard);
	}, [draft, selectedNode, key, defaultValue, typeGuard]);

	const setValue = useCallback((newValue: T): void => {
		updateDraft(key, newValue);
	}, [updateDraft, key]);

	return [value, setValue];
}
