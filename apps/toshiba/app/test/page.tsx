import { MainAreaSwitcher } from "../components/advanced/MainAreaSwitcher";
import { ProjectSidebar } from "../components/advanced/ProjectSidebar";
import "./page.scss";




export default function Chatbot(): JSX.Element {


  return (
    <main className="chatbot-advanced-container">
      {/* <Sidebar/> */}
      <ProjectSidebar/>
      <MainAreaSwitcher/>
    </main>
  );
}
