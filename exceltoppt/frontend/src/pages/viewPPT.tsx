import Image from 'next/image';
import { Inter } from 'next/font/google';
import { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import Header from '@/components/header';
import TopHeader from '@/components/topheader';
import Progressbar from '@/components/progressbar';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faPaperPlane } from '@fortawesome/free-solid-svg-icons';
import ChatWindow from '@/components/chatwindow';
import { useRouter } from 'next/router';
import { Avatar } from '@/components/Avatar';
import { IconShare } from '@/icons/IconShare';
import { TypeAComment } from "@/components/TypeAComment";



export default function Home() {
  const router = useRouter();
  const { ppt_file, summary, excel_file, sheet_name } = router.query;
  console.log(excel_file, sheet_name);
  const [question, setQuestion] = useState("");
  const [submittedQuestions, setSubmittedQuestions] = useState("");
  const [answer, setAnswer] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleQuestionSubmit = () => {
    setSubmittedQuestions(question);
    setIsLoading(true);
    handleSubmit(question, excel_file, sheet_name);
  };

  const handleSubmit = async (question: string, excel_file: string | string[] | undefined, sheet_name: string | string[] | undefined) => {
    try {
      // Ensure that excel_file and sheet_name are strings before using them

      const validExcelFile = excel_file ? (Array.isArray(excel_file) ? excel_file[0] : excel_file) : '';
      const validSheetName = sheet_name ? (Array.isArray(sheet_name) ? sheet_name[0] : sheet_name) : '';

      const q_params = "excel_file=" + encodeURIComponent(validExcelFile) + ".xlsx&manifest_file=" + encodeURIComponent(validSheetName) + "&question=" + encodeURIComponent(question);

      //const response = await axios.get(`http://localhost:8000/askcsvagent/?${q_params}`);
      const response = await axios.post(`http://localhost:8000/ask/`, {"query" : question, "context": summary});
      console.log(response);
      console.log(response.data)

      if (response.status === 200) {
        setAnswer(response.data);
        setIsLoading(false);
      }

    } catch (error) {
      console.error('Error getting Manifest Content:', error);
    }
  };

  const showSummary = () => {
    const doc_summary: any = summary ? summary : "";
    return doc_summary.replace(/\n/g, "<br />")
  }
  

  const handleDownload = async() => {

    try {
      console.log("downloading ppt..");
      const validPptFile = ppt_file ? (Array.isArray(ppt_file) ? ppt_file[0] : ppt_file) : '';
      const q_params = "ppt_path=" +encodeURIComponent(validPptFile);
      
      const response = await axios.get(`http://localhost:8000/downloadPPT/?${q_params}`, {
        responseType: 'blob', 
      });
  
     const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
  
      // Extract filename from Content-Disposition header
      const contentDisposition = response.headers['content-disposition'];
      const filenameMatch = contentDisposition && contentDisposition.match(/filename="(.+)"/);
      const filename = filenameMatch ? filenameMatch[1] : 'downloaded.pptx';
  
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
  
      /*if (link.parentNode) {
        link.click();
  
        // Clean up
        link.parentNode.removeChild(link);
        window.URL.revokeObjectURL(url);
      } else {
        console.error('Error: link.parentNode is null');
      }*/

     /* const link = document.createElement('a');
      link.href = URL.createObjectURL(response.data);
      link.download = validPptFile.split('/').pop() || 'download.pptx';
      link.click();*/
    } catch (error) {
      console.error('Error getting Manifest Content:', error);
    }
  };


  /*const handleDownload = async () => {
    try {

      console.log("downloading ppt..");
      const validPptFile = ppt_file ? (Array.isArray(ppt_file) ? ppt_file[0] : ppt_file) : '';
      const q_params = "ppt_path=" + encodeURIComponent(validPptFile);
      const response = await axios.get(`http://localhost:8000/downloadPPT/?${q_params}`);
      const url = window.URL.createObjectURL(new Blob([response.data]));

      // Create a link element and trigger a click to start the download
      const a = document.createElement('a');
      a.href = url;
      a.download = validPptFile.split('/').pop() || 'download.pptx';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);

    } catch (error) {
      console.error('Error downloding File: ' + error);
    }
  };*/
  useEffect(() => {
    const data = {
      ppt_file: ppt_file,
      summary: summary
    };

    const q_param = "";
  }, [ppt_file]);

  return (
    <div className="app-container">
      <TopHeader />
      <div className="upload-container-main2">
        <div className="breadcrumb-container">
          <a>Ingest</a>
          <span className="separator"></span>
          {'>'}
          <span className="current-page"> AI DeckBuilder</span>
        </div>
        <div className="progress-bar-container">
          <Progressbar current={3} />
        </div>
        <div className="button-container3">
          <div className="space-padding"></div>

        </div>
        <div className="manifest-header">PPT Preview</div>
        <div className="pptpreview-container">
          <div>

            <button className="action-button-align-right action-button" onClick={handleDownload}>Download</button>
            <div>
              <div><p dangerouslySetInnerHTML={{__html: showSummary()}} /></div>
            </div>
          </div>
          <div>
            
            <ChatWindow workbook_name={excel_file} sheet_name={sheet_name}/>
            
          </div>

        </div>
      </div>
    </div>
  );
}

