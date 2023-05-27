/* eslint-disable @next/next/no-img-element */
import { signIn, signOut, useSession } from "next-auth/react";
import React, { useEffect, useState } from "react";
import axios from "axios";
import jwt_decode from "jwt-decode";
import { FaSignOutAlt } from "react-icons/fa";

function externalSignOut() {
  let url = new URL("https://elevaite.iopex.ai/");
  url.searchParams.set("redirect_uri", "https://elevaite-ke.iopex.ai/");
  window.location.href = url.href;
}

export default function TopHeader() {
  const { data: session } = useSession();
  console.log({ session });
  const [name, setName] = useState();

  useEffect(() => {
    let params = new URL(window.location.href).searchParams;
    const token = params.get("token");
    if (!!token) {
      let decoded: any = jwt_decode(token);
      console.log(decoded);
      // let expTime = new Date(decoded.exp * 1000);
      // let currentTime = new Date().getTime();
      // if (currentTime < expTime.getTime()){
      //   console.log(expTime);
      //   setName(()=>decoded.name)
      // } else {
      //   window.location.href = "https://login.iopex.ai/login/google";
      // }
      setName(()=>decoded.name);
    } else {
      window.location.href = "https://login.iopex.ai/login/google";
    }
  }, []);
  return (
    <div className="frame-2">
      <div className="frame-3">
        <img
          className="frame-1000004664"
          src="img/frame-1000004664.svg"
          alt="Frame 1000004664"
        />
        <img className="line-1 line" src="img/line-1.svg" alt="Line 1" />
        <div className="product-support">Product Support</div>
      </div>
      <div className="frame-40505">
        <div className="frame-40502">
          <div className="find-answers">Find Answers</div>
          <img className="search" src="img/search.svg" alt="search" />
        </div>
        <div className="frame-40494">
          <div className="heroicons-solidbell">
            <div className="overlap-group">
              <img
                className="icon-notifications"
                src="img/vector.svg"
                alt="icon-notifications"
              />
              <div className="ellipse-963"></div>
            </div>
          </div>
          <img
            className="line-844 line"
            src="img/line-844.svg"
            alt="Line 844"
          />
          <img
            className="icon-question_mark"
            src="img/ci-help-questionmark.svg"
            alt="icon-question_mark"
          />
          <div className="frame-2-1">
            {name ? (
              <div className="name"> {name} </div>
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
