const PromptDetailActionButtons = () => {
  return (
	<div className="flex justify-end py-2 gap-2">
		<button className="btn btn-outline btn-small flex items-center justify-center gap-1 disabled:bg-gray-100 disabled:text-gray-400 disabled:hover:bg-gray-100 disabled:hover:text-gray-400 px-0">Save As</button>
		<button className="btn btn-outline btn-small flex items-center justify-center gap-1 disabled:bg-gray-100 disabled:text-gray-400 disabled:hover:bg-gray-100 disabled:hover:text-gray-400 px-0">
			Deploy
		</button>
		<button className="btn btn-primary btn-small flex items-center justify-center gap-1 disabled:bg-gray-100 disabled:text-gray-400 disabled:hover:bg-gray-100 disabled:hover:text-gray-400 px-0">
			<span>Run</span>
			<svg
				width="12"
				height="14"
				viewBox="0 0 12 14"
				fill="none"
				xmlns="http://www.w3.org/2000/svg"
				className="transition-colors duration-200 fill-white group-hover:fill-[#FF681F] disabled:fill-gray-400"
			>
				<path
					fill="currentColor" fillRule="evenodd" clipRule="evenodd"
					d="M3.33758 0.868244C3.34555 0.873558 3.35354 0.878889 3.36156 0.884236L10.3941 5.57256C10.5975 5.70819 10.7862 5.83394 10.9311 5.9508C11.0823 6.07276 11.2606 6.24188 11.3632 6.48928C11.4988 6.81628 11.4988 7.18379 11.3632 7.5108C11.2606 7.7582 11.0823 7.92732 10.9311 8.04927C10.7862 8.16613 10.5976 8.29187 10.3941 8.4275L3.3376 13.1318C3.08888 13.2977 2.86523 13.4468 2.67545 13.5496C2.48554 13.6525 2.22486 13.7702 1.92061 13.752C1.53145 13.7288 1.17194 13.5364 0.936737 13.2254C0.752855 12.9824 0.706114 12.7002 0.686406 12.4851C0.666711 12.2702 0.666729 12.0014 0.666749 11.7024L0.666751 2.32646C0.666751 2.31682 0.66675 2.30721 0.666749 2.29763C0.666729 1.9987 0.666711 1.7299 0.686406 1.51495C0.706114 1.29985 0.752855 1.01772 0.936737 0.774642C1.17194 0.463723 1.53145 0.271323 1.92061 0.248087C2.22486 0.22992 2.48554 0.347528 2.67545 0.450447C2.86522 0.553292 3.08886 0.70241 3.33758 0.868244Z"
				/>
			</svg>
		</button>
	</div>
  )
}
export default PromptDetailActionButtons