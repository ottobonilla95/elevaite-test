import { signIn } from 'next-auth/react';
import { useState } from 'react';

const Login = () => {
  const [showLoginFields, setShowLoginFields] = useState(false);

  // Google Handler Function
  async function handleGoogleSignIn() {
    signIn('google', { callbackUrl: "http://localhost:3000" });
  }

  
  const toggleLoginFields = () => {
    setShowLoginFields(!showLoginFields);
  };

  return (
    <div className="login-container">
      <div className="login-box">
        <h2>Campaign Creatives Management</h2>
        <button className="google-sign-in-button" onClick={handleGoogleSignIn}>
          <span style={{ display: 'flex', alignItems: 'center' }}>
            <span>Sign in with Google</span>
            <img src="img/google.svg" alt="Google Logo" style={{ marginLeft: '10px' }} />
          </span>
        </button>
        <div className="space-padding"></div>
        <hr className="sidebar-divider"></hr>
        <div className="space-padding"></div>

        {showLoginFields ? (
          <>
            <div className="input-field">
              <label htmlFor="username">Username:</label>
              <input type="text" id="username" name="username" />
            </div>
            <div className="input-field">
              <label htmlFor="password">Password:</label>
              <input type="password" id="password" name="password" />
            </div>
            <button className="button-align-center work-bench-button2">Login</button>
          </>
        ) : (
            <div>
                Already a member? 
                <div className="space-padding"></div>
                <button className="button-align-center work-bench-button2" onClick={toggleLoginFields}>
                    Sign up
                </button>
          </div>
        )}

        <div className="space-padding"></div>
      </div>
    </div>
  );
};

export default Login;
