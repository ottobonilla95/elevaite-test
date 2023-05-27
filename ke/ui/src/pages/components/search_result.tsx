/* eslint-disable react-hooks/exhaustive-deps */
import { useRef, useState, useEffect } from "react";
import TextareaAutosize from "@mui/base/TextareaAutosize";
import SearchTextArea from "./searchtextarea";
import SearchMetaData from "./searchmetadata";
import arrowUp from "../../../public/arrow_up.png";
import arrowRight from "../../../public/right.png";
import arrowLeft from "../../../public/left.png";
import Image from "next/image";
import { Button, Dialog, DialogActions, DialogContent, DialogContentText, DialogTitle, TextField, MenuItem, CircularProgress } from "@mui/material";
import axios from "axios";
import 'react-quill/dist/quill.snow.css';
import dynamic from "next/dynamic";
// const QuillNoSSRWrapper = dynamic(import('react-quill'), {	
// 	ssr: false,
// 	loading: () => <p>Loading ...</p>,
// 	});
// const QuillNoSSRWrapper = dynamic(async () => {
//   const ReactQuill = await import('react-quill');
//   const { Quill } = ReactQuill.default;
//   const Block = Quill.import('blots/block');
//   Block.tagName = 'base';
//   Quill.register(Block);

//   return ReactQuill;
// }, { ssr: false, loading: () => <p>Loading ...</p> });



// TODO: Split this page into two, search page & results page

export default function SearchResult() {
  // Dummy result array for local development & verification
  const resultArr = ['mattis enim ut tellus elementum sagittis vitae et leo duis ut diam quam nulla porttitor massa id neque aliquam vestibulum morbi blandit cursus risus at ultrices mi tempus imperdiet nulla malesuada pellentesque elit eget gravida cum sociis natoque penatibus et magnis dis parturient montes nascetur ridiculus mus mauris vitae ultricies leo integer malesuada nunc vel risus commodo viverra maecenas accumsan lacus vel facilisis volutpat est velit egestas dui id ornare arcu odio ut sem nulla pharetra diam sit amet nisl suscipit adipiscing bibendum est ultricies integer quis auctor elit sed vulputate mi sit amet mauris commodo quis imperdiet massa tincidunt', 'turpis egestas integer eget aliquet nibh praesent tristique magna sit amet purus gravida quis blandit turpis cursus in hac habitasse platea dictumst quisque sagittis purus sit amet volutpat consequat mauris nunc congue nisi vitae suscipit tellus mauris a diam maecenas sed enim ut sem viverra aliquet eget sit amet tellus cras adipiscing enim eu turpis egestas pretium aenean pharetra magna ac placerat vestibulum lectus mauris ultrices eros in cursus turpis massa tincidunt dui ut ornare lectus sit amet est placerat in egestas erat imperdiet sed euismod nisi porta lorem mollis aliquam ut porttitor leo a diam sollicitudin tempor id eu  ', 'nec ullamcorper sit amet risus nullam eget felis eget nunc lobortis mattis aliquam faucibus purus in massa tempor nec feugiat nisl pretium fusce id velit ut tortor pretium viverra suspendisse potenti nullam ac tortor vitae purus faucibus ornare suspendisse sed nisi lacus sed viverra tellus in hac habitasse platea dictumst vestibulum rhoncus est pellentesque elit ullamcorper dignissim cras tincidunt lobortis feugiat vivamus at augue eget arcu dictum varius duis at consectetur lorem donec massa sapien faucibus et molestie ac feugiat sed lectus vestibulum mattis ullamcorper velit sed ullamcorper morbi tincidunt ornare massa eget egestas purus viverra accumsan in nisl nisi', 'in hac habitasse platea dictumst quisque sagittis purus sit amet volutpat consequat mauris nunc congue nisi vitae suscipit tellus mauris a diam maecenas sed enim ut sem viverra aliquet eget sit amet tellus cras adipiscing enim eu turpis egestas pretium aenean pharetra magna ac placerat vestibulum lectus mauris ultrices eros in cursus turpis massa tincidunt dui ut ornare lectus sit amet est placerat in egestas erat imperdiet sed euismod nisi porta lorem mollis aliquam ut porttitor leo a diam sollicitudin tempor id eu nisl nunc mi ipsum faucibus vitae aliquet nec ullamcorper sit amet risus nullam eget felis eget nunc'];
  // Initializing state variables
  const meta: string[] = ['Document Type', 'Product', 'Version'];
  const [metaState, setMetaState] = useState<string[]>(['', '', ''])
  const [ask, setAsk] = useState<string>("");
  // const [chunks, setChunks] = useState<string[]>(['']);
  const [chunks, setChunks] = useState<string[]>([]);
  const [chunkSize, setChunkSize] = useState<number[]>([]);
  const [summarySize, setSummarySize] = useState<number[]>([]);
  const [summaryChunks, setSummaryChunks] = useState<string[]>([]);
  const [totalChunkSize, setTotalChunkSize] = useState<number>(0);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isVisible, setIsVisible] = useState<boolean>(false);
  const [totaltokenlen, setTotaltokenlen] = useState<number>(0);
  const [result, setResult] = useState<any>();
  const [open, setOpen] = useState<boolean>(false);
  const handleOpen = () => setOpen(true);
  const handleClose = () => setOpen(false);
  const [rteOpen, setRteOpen] = useState<boolean>(false);
  const [titleError, setTitleError] = useState<string>('Error');
  const handleRteOpen = () => setRteOpen(true);
  const handleRteClose = () => setRteOpen(false);
  const [rteTitle, setRteTitle] = useState<string>('');
  const [modaltitle, setModaltitle] = useState<string>('');
  const [rteContent, setRteContent] = useState<string>('');
  const [rteIndex, setRteIndex] = useState<number>(-1);
  const [errorText, setErrorText] = useState<string>('');

  // Refs for network calls
  const fetchResult = useRef(() => { });
  const saveResult = useRef(() => { });
  const calculateChunk = useRef(() => { });
  const style = {
    position: 'absolute' as 'absolute',
    top: '50%',
    left: '50%',
    transform: 'translate(-50%, -50%)',
    width: 400,
    bgcolor: 'background.paper',
    border: '2px solid #000',
    boxShadow: 24,
    p: 4,
  };

  console.log("chunks", chunks.length)
  // const Rtecontent = (event: any) => {
  //   console.log("event", event)
  //   const div = document.createElement('div');
  //   div.innerHTML = event;
  //   const new_text = div.innerHTML.replace(/<p>/g, '').replace(/<\/p>/g, '');
  //   console.log("inner", new_text)
  //   setRteContent(new_text);
  // }
  // parse result and store in state
  const setOutputResult = (inputData: any) => {
    const content = JSON.parse(inputData.data.content);
    console.log(content)
    const resArr = content.Chunks.map((c: any) => c.Text);
    setChunks(() => [...resArr]);
    setTotalChunkSize(() => content.TotalTokens);
    setChunkSize(() => [...content.Chunks.map((c: any) => c.Size)]);
    const resMeta = [content.DocumentType, content.Product, content.Version];
    setMetaState(() => [...resMeta]);
    setSummaryChunks(() => []);
    setSummarySize(() => []);
  };

  const handleClick = (event: any) => {
    setChunks([])
    setChunkSize([])
    const regex = new RegExp('(https?://)?([\\da-z.-]+)\\.([a-z.]{2,6})[/\\w .-]*/?');
    if (ask.trim() != "" && regex.test(ask.trim())) {
      setIsLoading(() => true);
      setIsVisible(true);
      // setChunks(()=>[...resultArr]);
      fetchResult.current();
    } else {
      setErrorText('Please provide a valid domain');
      handleOpen();
      setIsVisible(false);
    }
  };

  // Webscrape API call
  fetchResult.current = async () => {
    setTitleError("Error")
    return await axios
      .post("https://elevaite-ke.iopex.ai/webscrap", JSON.stringify({ url: ask }))
      .then((res) => {
        console.log(ask, res);
        setResult(res);
        console.log("res",result)
        setOutputResult(res);
      }).catch((error) => {
        console.log("Error occured", error);
        // setDemoData(demoData); 
      });
  };

  useEffect(()=>{
    setTotaltokenlen(() => chunkSize.reduce((acc, s) => acc + s, 0));
    return () => {
      setTotaltokenlen(0)
    };
  },[chunks])


  // Final Vectorize API call
  saveResult.current = async () => {
    let save = JSON.parse(result.data.content);
    save['Chunks'] = summaryChunks.map((s, i) => { return { Chunk: i + 1, Size: summarySize[i], Text: s } });
    save['TotalTokens'] = summarySize.reduce((acc, s) => acc + s, 0);
    save['Chunks'] = save['Chunks'].filter((c: any) => !!c.Text);
    save['DocumentType'] = metaState[0]
    save['Product'] = metaState[1]
    save['Version'] = metaState[2]
    console.log("res2",save)
    return await axios
      .post("https://elevaite-ke.iopex.ai/savecontent", { content: JSON.stringify(save) })
      .then((res) => {
        console.log(res);
        setErrorText(res.data.response);
        handleOpen();
      }).catch((error) => {
        console.log("Error occured", error);
        setErrorText('Error Occured');
        handleOpen();
      });
  };

  const change = (event: any) => {
    setAsk(() => event.target.value);
  };
  const changeMeta = (id: number, event: any) => {
    let localMeta = metaState;
    localMeta[id] = event.target.value;
    setMetaState(() => [...localMeta]);
  };
  console.log("meta",metaState)

  const calculateTotalChunks = () => {
    setTotalChunkSize(() => chunks.map(c => c.length).reduce((acc, s) => acc + s, 0));
  };
  const changeChunks = (id: number, event: any) => {
    let localChunks = chunks;
    localChunks[id] = event.target.value;
    setChunks(() => [...localChunks]);
    calculateTotalChunks();
  };
  const handleKeyDown = (e: any) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleClick(e);
    }
  };
  const handleAdd = () => {
    setChunks(() => [...chunks, '']);
  };

  const moveUp = (index: number, chunk: string[], size: number[]) => {
    chunk[index - 1] += chunk[index];
    chunk.splice(index, 1);
    size[index - 1] += size[index];
    size.splice(index, 1);
    setChunks(Array.from(chunk));
    setChunkSize(Array.from(size));
  };

  const moveDown = (index: number, chunk: string[], size: number[]) => {
    chunk[index] += chunk[index + 1];
    chunk.splice(index + 1, 1);
    size[index] += size[index + 1];
    size.splice(index + 1, 1);
    setChunks(Array.from(chunk));
    setChunkSize(Array.from(size));
  };

  // index: index of array, order: true - move up 
  const mergeChunks = (index: number, order: boolean) => {
    let localChunks = Array.from(chunks);
    let localChunkSize = Array.from(chunkSize);
    if (index == 0) {
      if (chunks.length == 1) {
        setErrorText('Please add another chunk to merge down');
        handleOpen();
        return;
      }
      moveDown(index, localChunks, localChunkSize);
    } else if (order) {
      moveUp(index, localChunks, localChunkSize);
    } else {
      if (chunks.length - 1 == index) {
        moveUp(index, localChunks, localChunkSize);
      }
      moveDown(index, localChunks, localChunkSize);
    }
  };
  // Move chunks to summarize
  // const summarizeChunks = (index: number) => {
  //   let localSummary = Array.from(summaryChunks);
  //   for (let i = localSummary.length; i < index; i++) {
  //     localSummary[i] = '';
  //   }
  //   localSummary[index] = chunks[index];
  //   let localChunkSize = Array.from(summarySize);
  //   for (let i = localChunkSize.length; i < index; i++) {
  //     localChunkSize[i] = 0;
  //   }
  //   localChunkSize[index] = chunkSize[index];
  //   setSummaryChunks(() => [...localSummary]);
  //   setSummarySize(() => [...localChunkSize]);
  // };

  const summarizeChunks = (index: number) => {
    console.log(index);
    console.log("size", chunkSize[index]);
    console.log("tsize", chunkSize);
    setSummaryChunks((prevSummaryChunks) => {
      const localSummary = [...prevSummaryChunks];
      if (localSummary[index]) {
        localSummary[index] = chunks[index];
      } else {
        localSummary.push(chunks[index]);
      }
      return localSummary;
    });
  
    setSummarySize((prevSummarySize) => {
      const localChunkSize = [...prevSummarySize];
      if (localChunkSize[index]) {
        localChunkSize[index] = chunkSize[index];
      } else {
        localChunkSize.push(chunkSize[index]);
      }
      return localChunkSize;
    });
  };
  

  

  // Move summary to chunks
  // const summaryToChunks = (index: number) => {
  //   let localChunks = Array.from(chunks);
  //   localChunks[index] = summaryChunks[index];
  //   setChunks(() => [...localChunks]);
  // }

  const summaryToChunks = (index: number) => {
    const updatedArray = [...summaryChunks]; 
    const updatedtokenArray = [...summarySize];
    updatedArray.splice(index, 1);
    updatedtokenArray.splice(index, 1);
    setSummaryChunks(updatedArray);
    setSummarySize(updatedtokenArray);
  }

  // Final Save
  const vectorize = () => {
    if (summaryChunks.length == 1 && !summaryChunks[0]) {
      setErrorText('Please Summarize atleast one Chunk');
      handleOpen();
      return;
    }
    setTitleError("Success")
    saveResult.current();
  };
  const handleMoveAll = () => {
    setSummaryChunks(() => [...chunks]);
    setSummarySize(() => [...chunkSize]);
  };

  // Set RTE editor open & store necessary data for it
  const editRte = (index: number) => {
    setRteTitle(`Chunk ${index + 1} - ${chunkSize[index]} tokens`);
    setModaltitle(`Chunk ${index + 1}`);
    setRteContent(chunks[index]);
    setRteIndex(index);
    handleRteOpen();
  };

  // const addRte = (index:number) => {
  //   setRteTitle(`Chunk ${index+1} - ${chunkSize[index]} tokens`);

  //   setChunks(["",...chunks])
  //   // setRteContent(chunks[index]);
  //   // setRteIndex(index);
  //   // handleRteOpen();
  // };
  function addRte(index: number): void {
    const element = { Chunk: 0, Size: 0, Text: " " };
    console.log("index", index)
    setChunks(prevChunkArray => [...prevChunkArray.slice(0, index + 1), element.Text, ...prevChunkArray.slice(index + 1)]);
    setChunkSize(prevSizeArray => [...prevSizeArray.slice(0, index + 1), element.Size, ...prevSizeArray.slice(index + 1)]);
  }

  const delRte = (index: number) => {
    console.log(index)
    const updatedArray = [...chunks];  // Create a copy of the original array
    updatedArray.splice(index, 1);    // Remove the element at the specified index
    setChunks(updatedArray);         // Update the state with the modified array
    const updatedArray2 = [...chunkSize];  // Create a copy of the original array
    updatedArray2.splice(index, 1);    // Remove the element at the specified index
    setChunkSize(updatedArray2);
  };

  // Close RTE editor & clear stored data
  const handleDone = () => {
    let localChunks = Array.from(chunks);
    localChunks[rteIndex] = rteContent;
    setChunks(() => [...localChunks]);
    setRteTitle('');
    setRteContent('');
    setRteIndex(-1);
    handleRteClose();
  };

  const setCaluclatedChunk = (size: number) => {
    let localChunkSize = Array.from(chunkSize);
    localChunkSize[rteIndex] = size;
    setChunkSize(localChunkSize);
  }

  // Calculate Chunks call
  const mycalculateChunk = async (rteContent: string) => {
    try {
      const response = await axios.post("https://elevaite-ke.iopex.ai/chunksize", JSON.stringify({ content: rteContent }));
      console.log(ask, response);
      setCaluclatedChunk(JSON.parse(response.data.chunksize));
      handleDone()
    } catch (error) {
      console.log("Error occurred", error);
      // handleDone();
    }

  };
  // const handleInputChange = (event: any) => {
  //   const inputValue = event.target.value;
  //   setRteContent(inputValue);

  //   if (inputValue.length > 100) {
  //     event.target.style.color = 'red';
  //   } else {
  //     event.target.style.color = 'black';
  //   }

  // };
  const [fontSize, setFontSize] = useState('medium');

  const handleInputChange = (event: any) => {

    setRteContent(event.target.value);
  };

  const handleFontSizeChange = (event: any) => {
    setFontSize(event.target.value);
  };

  const calculateRows = () => {
    const lineBreaks = (rteContent.match(/\n/g) || []).length;
    return Math.min(lineBreaks + 20, 10); // Adjust the maximum number of rows if needed
  };

  const FontSizeOptions = [
    { value: 'small', label: 'Small' },
    { value: 'medium', label: 'Medium' },
    { value: 'large', label: 'Large' },
  ];


  return (
    <>
      <div className="band-flex">
        <div className="band-top">I am here</div>
        <div className="band-bottom">i am bottom</div>
      </div>
      <div className="band"></div>
      <div className="chat-container">
        <div className="chat-header">
          <p> Enter the URL to Scoop </p>
          <div className="container-body">
            <TextareaAutosize
              minRows={1}
              maxRows={1}
              className="chat-input1"
              onChange={change}
              value={ask}
              onKeyDown={handleKeyDown}
              placeholder="Enter the URL"
            />
          </div>
          <button className="button" onClick={handleClick} disabled={ask.trim() == ""}>
            Submit
          </button>
        </div>

        <div className="band-top1">
          <div className={isVisible ? "grand-parent1 visible" : "grand-parent1 invisible"}>
            <div className="parent-container">
              <div className="grid lablename grid-cols-3 gap-x-8">
                {metaState.map((m: string, id: number) => {
                  return <SearchMetaData key={id} change={changeMeta.bind(metaState, id)} classId={id} placeHolder={meta[id]} ask={m} readonly={false} />;

                })}
              </div>
            </div>
          </div>
        </div>

        <div className="final-container">
          <div className={isVisible ? "grand-parent visible" : "grand-parent invisible"}>
            <div className="grid grid-cols-4 Divbox gap2 line"> <div></div><div></div>
              <div className="topbar">Total Chunks : <div className="box">{chunks.length}</ div ></div>  <div className="topbar1">Total token size: <div className="box">{totaltokenlen}</ div ></ div >
            </div>
            <div className="parent-container">
              {chunks.length === 0 && <div className="spinner">
              <CircularProgress />
              </div>}
              <div className="rcorners1">
                <div className="grid grid-cols-2 searchDiv gap-x-24">
                  <div><span className="doc"></span>
                    Document Chunks
                    <button className="button Btnmove" onClick={handleMoveAll}>
                      <span className="move"></span> Summarize
                    </button>
                    {chunks.length !== 0 && chunks.map((c: string, id: number) => {
                      if (typeof c == "number") {
                        return (<></>);
                      }
                      return (<div key={'divchunk' + (id + 1)}> <div>&nbsp;</div>
                        {/* <p className="title">Chunk {id+1} - {chunkSize[id]} tokens</p> */}
                        <div className="flex">
                          <SearchTextArea key={'chunk' + (id + 1)} change={changeChunks.bind(chunks, id)} placeHolder={''} classId={id} ask={c} minRows={4} maxRows={4} readonly={true} label={`Chunk ${id + 1} - ${chunkSize[id]} tokens`} rteEdit={editRte.bind(chunks, id)} visiblethreebtn={true} rteAdd={addRte.bind(chunks, id)} rteDel={delRte.bind(chunks, id)} />
                          <div className="moveBtn">
                            <span className="moveBtn1">{id > 0 && id < chunks.length - 1 ? <Image alt="arrow up" className="rotate pointer" src={arrowUp} onClick={() => { mergeChunks(id, true) }} /> : <></>}</span>
                            <span className="moveBtn1"><Image alt="arrow down" src={arrowUp} className={(id == chunks.length - 1 ? 'rotate pointer ' : 'pointer ') + (chunks.length == 1 ? 'nopointer' : '')} onClick={() => { mergeChunks(id, false) }} /></span>
                            <span className="moveBtn1"><Image alt="right arrow" className="pointer" src={arrowRight} onClick={() => { summarizeChunks(id) }} /></span>
                          </div>
                        </div>
                      </div>);
                    })}
                    
                    <button className="button addBtn" onClick={handleAdd}>
                      Add Chunk
                    </button>
                  </div>
                  <div>
                    <span className="doc"></span>Chunk Summary <button className="button Btnmove1" onClick={vectorize}>
                      <span className="vector"></span>  Vectorize
                    </button>
                    {summaryChunks.map((c: string, id: number) => {
                      if (typeof c == "number") {
                        return (<></>);
                      }
                      if (c == '') {
                        return null;
                      }
                      return (<div key={'divsummary' + (id + 1)}> <div>&nbsp;</div>
                        {/* <p>Chunk {id+1}</p> */}
                        <div className="flex">
                          <div className="moveBtn01">
                            <span className="moveBtn2"><Image alt="left arrow" className="pointer" src={arrowLeft} onClick={() => { summaryToChunks(id) }} /></span>
                          </div>
                          <SearchTextArea key={'chunkres' + (id + 1)} change={changeChunks.bind(chunks, id)} placeHolder={''} classId={id} ask={c} minRows={4} maxRows={4} readonly={true} label={`Chunk ${id + 1} - ${summarySize[id]} tokens`} visiblethreebtn={false} rteEdit={editRte.bind(chunks, id)} rteAdd={addRte.bind(chunks, id)} rteDel={delRte.bind(chunks, id)} />
                        </div>
                      </div>);
                    })}

                  </div>
                </div>
              </div>
            </div>
          </div>
          <Dialog
            open={open}
            onClose={handleClose}
            aria-labelledby="alert-dialog-title"
            aria-describedby="alert-dialog-description"
          >
            <DialogTitle id="alert-dialog-title">
              {titleError}
            </DialogTitle>
            <DialogContent>
              <DialogContentText id="alert-dialog-description">
                {errorText}
              </DialogContentText>
            </DialogContent>
            <DialogActions>
              <Button onClick={handleClose} >
                Okay
              </Button>
            </DialogActions>
          </Dialog>
          <Dialog
            open={rteOpen}
            onClose={handleRteClose}
            aria-labelledby="alert-dialog-title"
            aria-describedby="alert-dialog-description"
          >
            <DialogTitle id="alert-dialog-title">
              {modaltitle}
            </DialogTitle>
            <DialogContent style={{ overflow: 'hidden' }}>
              <DialogContentText style={{ display: "flex", flexDirection: "row", gap: 2 }} id="alert-dialog-description">
                <TextField id="standard-basic" variant="standard"
                  select
                  value={fontSize}
                  onChange={handleFontSizeChange}
                  label="Font Size"
                >
                  {FontSizeOptions.map((option) => (
                    <MenuItem key={option.value} value={option.value}>
                      {option.label}
                    </MenuItem>
                  ))}
                </TextField>
                <TextField
                  multiline
                  rows={calculateRows()}
                  value={rteContent}
                  onChange={handleInputChange}
                  InputProps={{
                    style: {
                      minHeight: '260px',
                      width: '450px',
                      padding: '10px',
                      fontSize: fontSize === 'small' ? '13px' : fontSize === 'large' ? '18px' : 'inherit',
                    },
                  }}
                />
              </DialogContentText>
            </DialogContent>
            <DialogActions>
              <Button onClick={() => mycalculateChunk(rteContent)} >
                Done
              </Button>
            </DialogActions>
          </Dialog>
        </div>
      </div>
    </>
  );
}
