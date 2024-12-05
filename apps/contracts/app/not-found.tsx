/* eslint-disable unicorn/filename-case -- nextJS demands that filename */
import "./not-found.scss";



export default function NotFound(): JSX.Element {
    return (
      <div className="not-found-container">
        <h1 className="page-code" title="Well, at least it's not 500...">404</h1>
        <h2>This page isn&apos;t available.</h2>
        <p>Check your URL, or get back on track with the breadcrumbs above.</p>
      </div>
    )
}