import React from 'react'
import { FaSignOutAlt, FaShoppingCart } from "react-icons/fa";
import { useSession, signOut } from 'next-auth/react';
import { useRouter } from 'next/router';

type HeaderProps = {
  selectedImageCount: number;
  selectedImages: string[] | null
};



const header: React.FC<HeaderProps> = ({selectedImageCount, selectedImages}) => {

  const{data:session} = useSession();
  const router = useRouter();

  const handleSignOut = async() =>{
    await signOut({ callbackUrl: "/login"});
  };

  const handleShoppingCartClick = () => {
    const formData = {
      url: selectedImages,
      count: selectedImageCount
    };

    router.push({
      pathname: '/shoppingCart',
      query: formData
    });
  }
  
  return (
    <div className="frame-2">
        <div className="frame-3">
            <img
                className="frame-1000004664"
                src="img/frame-1000004664.svg"
                alt="Frame 1000004664"
            />
            <img className="line-1 line" src="img/line-1.svg" alt="Line 1" />
            <div className="product-support">Campaign Creatives Management</div>
        </div>
        
        <div className="frame-2-1">
            
          <button
            style={{ width: "25px", height: "25px", position: "relative" }}
            onClick = {handleShoppingCartClick}
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 576 512"
              fill="currentColor"
            >
              <path d="M96 0C107.5 0 117.4 8.19 119.6 19.51L121.1 32H541.8C562.1 32 578.3 52.25 572.6 72.66L518.6 264.7C514.7 278.5 502.1 288 487.8 288H170.7L179.9 336H488C501.3 336 512 346.7 512 360C512 373.3 501.3 384 488 384H159.1C148.5 384 138.6 375.8 136.4 364.5L76.14 48H24C10.75 48 0 37.25 0 24C0 10.75 10.75 0 24 0H96zM128 464C128 437.5 149.5 416 176 416C202.5 416 224 437.5 224 464C224 490.5 202.5 512 176 512C149.5 512 128 490.5 128 464zM512 464C512 490.5 490.5 512 464 512C437.5 512 416 490.5 416 464C416 437.5 437.5 416 464 416C490.5 416 512 437.5 512 464z" />
            </svg>

            {selectedImageCount > 0 && 
            (<div
              style={{
                color: "white",
                width: "10px",
                height: "1.5rem",
                position: "absolute",
                bottom: 0,
                right: 0,
                transform: "translate(25%, 25%)",
              }}
            >
              {selectedImageCount}
            </div>)}
          </button>
              
              <div className="name">{session?.user?.name}</div>
            
            <button onClick ={handleSignOut} className="logout-button"> 
            <FaSignOutAlt height="14px" width="14px" color="white"/>
            </button>
          </div>
      </div>
    
  )
}

export default header


