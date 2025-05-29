import './PromptLoading.scss';

interface PromptLoadingProps extends React.HTMLAttributes<HTMLDivElement> {
	width?: number;
	height?: number;
}

function PromptLoading(props: PromptLoadingProps): JSX.Element {
  const width = `${(props.width ?? 50)}px`;
  const height = `${(props.height ?? 50)}px`;
  return (
	<div className={`${props.className} prompt-loading`} style={{width: width, height: height}}></div>
  )
}
export default PromptLoading