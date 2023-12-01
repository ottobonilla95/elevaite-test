/* eslint-disable @next/next/no-img-element */
import { signIn, signOut, useSession } from "next-auth/react";
import React, { useEffect, useState } from "react";
import axios from "axios";
import jwt_decode from 'jwt-decode';
import { FaSignOutAlt } from "react-icons/fa";

function externalSignOut() {
  let url = new URL("https://elevaite.iopex.ai/");
  // url.searchParams.set("redirect_uri", "http://localhost:3000/");
  window.location.href = url.href;
}

export default function TopHeader() {
  const{data:session} = useSession();
  let name = session?.user?.name
  console.log("session details: ", session);
  //const [name, setName] = useState("Sucharitha Rumesh");

 {/*} useEffect(() => {
    let params = new URL(window.location.href).searchParams;
    const token = params.get("token");
    if (!!token) {
      let decoded: any = jwt_decode(token);
      // let expTime = new Date(decoded.exp * 1000);
      // let currentTime = new Date().getTime();
      // if (currentTime < expTime.getTime()){
      //   console.log(expTime);
      //   setName(()=>decoded.name)
      // } else {
      //   window.location.href = process.env.NEXT_PUBLIC_LOGIN_API;
      // }
      setName(()=>decoded.name);
    } else {
      console.log(process.env.NEXT_PUBLIC_LOGIN_API);
      if (!!process.env.NEXT_PUBLIC_LOGIN_API){
        window.location.href = process.env.NEXT_PUBLIC_LOGIN_API;
      }
    }
  }, []);*/}
  return (
    <div className="th-frame-2">
      <div className="th-frame-3">
        <img
          className="th-frame-1000004664"
          src="img/frame-1000004664 copy.svg"
          alt="Frame 1000004664"
        />
        <img className="th-line-1 line" src="img/line-1.svg" alt="Line 1" />
        <div className="th-product-support">AI Deck Builder</div>
      </div>
      <div className="th-frame-40505">
        <div className="th-frame-40502">
          <div className="th-find-answers">Find Answers</div>
          <img className="th-search" src="img/search.svg" alt="search" />
        </div>
        <div className="th-frame-40494">
          <div className="th-heroicons-solidbell">
            <div className="th-overlap-group">
              <img
                className="th-icon-notifications"
                src="img/Vectors.svg"
                alt="icon-notifications"
              />
              <div className="th-ellipse-963"></div>
            </div>
          </div>
          <img
            className="th-line-844 line"
            src="img/line-844.svg"
            alt="Line 844"
          />
          <img
            className="th-icon-question_mark"
            src="img/ci-help-questionmark.svg"
            alt="icon-question_mark"
          />
          <div className="th-frame-2-1">
            {name ? (
              <div className="th-name"> {name} </div>
            ) : (
              null
            )}
            {/* <button onClick={externalSignIn}>Sign Out</button> */}
            {/* {session?.user ? (
              <>
                <div className="name"> {session?.user?.name} </div>
                <button onClick={() => signOut()}> Sign out</button>
              </>
            ) : (
              <button onClick={externalSignIn}>Sign In</button>
            )} */}
            <button className="logout-button" onClick={() => externalSignOut()}> 
            <FaSignOutAlt height={20} width={20} color="white"/>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
