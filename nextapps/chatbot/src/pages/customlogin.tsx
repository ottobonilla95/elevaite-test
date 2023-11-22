import { useState } from 'react';
import axios from 'axios';
import { signIn } from 'next-auth/react'
import { useRouter } from 'next/router';

const CustomLogin = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showSignUp, setShowSignUp] = useState(false);
  const [name, setName] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  const [nameError, setNameError] = useState('');
  const [emailError, setEmailError] = useState('');
  const [passwordError, setPasswordError] = useState('');
  const [confirmPasswordError, setConfirmPasswordError] = useState('');
  const [authorizationError, setAuthorizationError] = useState('');

  const router = useRouter();

  // Google Handler Function
  async function handleGoogleSignIn() {
    // Redirect to Google authentication page
  }

  // Custom Login Validation API- have to update the URL
  const handleCustomLogin = async () => {

    try{
      const response = await axios.get('http://localhost:3000/api/authUser', {
        params: {
          userName: email,
          password: password
        },
      });
      setAuthorizationError('');

    } catch (error) {
      console.log("Error: " + error);
      setAuthorizationError("Username and Password is incorrect");
      
    }
    
  };

  //not used
  const handleSignUpClick = () => {
    // Toggle the showSignUp state to display the sign-up form
    setNameError('');
    setEmailError('');
    setPasswordError('');
    setConfirmPasswordError('');
    setShowSignUp(!showSignUp);

  };

  //not used - incomplete
  const handleCustomSignUp = () => {
    // Validation
    let isValid = true;

    if (!name.trim()) {
      setNameError('Name is required');
      isValid = false;
    } else {
      setNameError('');
    }

    if (!email.trim()) {
      setEmailError('Email is required');
      isValid = false;
    } else {
      setEmailError('');
    }

    if (!password.trim()) {
      setPasswordError('Password is required');
      isValid = false;
    } else {
      setPasswordError('');
    }

    if (password !== confirmPassword) {
      setConfirmPasswordError('Passwords do not match');
      isValid = false;
    } else {
      setConfirmPasswordError('');
    }

    if (isValid) {
      // All fields are valid, you can proceed with sign-up logic here
      const user = {
        name,
        email,
        password,
      };
      console.log('User data:', user);

      // Clear the form
      setName('');
      setEmail('');
      setPassword('');
      setConfirmPassword('');
    }

  }
  
  return (
    <div className="login-container">
      <div className="login-box">
        <div className="icon-container">
          <img
            className="frame-1000004664"
            src="img/frame-1000004664.svg"
            alt="Frame 1000004664"
          />
        </div>
        {!showSignUp ? ( 
          <>
            <div className="input-field">
              <input
                type="text"
                id="username"
                name="username"
                placeholder="Email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>
            <div className="input-field">
              <input
                type="password"
                id="password"
                name="password"
                placeholder="Password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>
            <button className="login-button" onClick={handleCustomLogin}>
              Login
            </button>
            {authorizationError && <div className="error-message red-text">{authorizationError}</div>}
            {/*
            <p style={{ padding: '10px 0', alignItems: 'center', color: 'white' }}>
              Don't have an account yet?{' '}
              <span className="link-button" onClick={handleSignUpClick}>
                Sign up
              </span>
            </p>
          */}
            <hr className="divider"></hr>
            <button className="google-sign-in-button" onClick={handleGoogleSignIn}>
              <span style={{ display: 'flex', alignItems: 'center' }}>
                <span>Sign in with Google</span>
                <img src="img/google.svg" alt="Google Logo" style={{ marginLeft: '10px' }} />
              </span>
            </button>
            
          </>
        ) : (
          // Show sign-up form
          <>
            <div className="input-field">
              
                <input
                  type="text"
                  id="name"
                  name="name"
                  placeholder="Name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                />
              
                {nameError && <div className="error-message red-text">{nameError}</div>}
              
            </div>
            <div className="input-field">
              <input
                type="text"
                id="email"
                name="email"
                placeholder="Email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
              {emailError && <div className="error-message red-text">{emailError}</div>}
            </div>
            <div className="input-field">
              <input
                type="password"
                id="password"
                name="password"
                placeholder="Password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>
            {passwordError && <div className="error-message red-text">{passwordError}</div>}
            <div className="input-field">
              <input
                type="password"
                id="confirmPassword"
                name="confirmPassword"
                placeholder="Confirm Password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
              />
              {confirmPasswordError && <div className="error-message red-text">{confirmPasswordError}</div>}
            </div>
            <button className="login-button" onClick={handleCustomSignUp}>
              Sign up
            </button>
            <p style={{ padding: '10px 0', alignItems: 'center', color: 'white' }}>
              Already have an account?{' '}
              <span className="link-button" onClick={handleSignUpClick}>
                Login
              </span>
            </p>
            {authorizationError && <div className="error-message red-text">{authorizationError}</div>}
            <hr className="divider"></hr>
            <button className="google-sign-in-button" onClick={handleGoogleSignIn}>
              <span style={{ display: 'flex', alignItems: 'center' }}>
                <span>Sign in with Google</span>
                <img src="img/google.svg" alt="Google Logo" style={{ marginLeft: '10px' }} />
              </span>
            </button>
          </>
        )}
      </div>
    </div>
  );
};

export default CustomLogin;
