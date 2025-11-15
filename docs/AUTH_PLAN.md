# TripFlow Authentication System - Implementation Plan

## Overview
Implement comprehensive user authentication with social logins (Google, Microsoft) and email/password authentication.

## Architecture

### Authentication Flow
```
User → Frontend Login Page → OAuth Provider (Google/Microsoft)
                           ↓
                    Backend receives token
                           ↓
                    Verify with provider
                           ↓
                    Create/update user
                           ↓
                    Issue JWT token
                           ↓
                    Frontend stores token
                           ↓
                    All API requests include JWT
```

### Technology Stack
- **Backend:** FastAPI with `python-jose` (JWT), `passlib` (password hashing)
- **OAuth:** `authlib` for OAuth2 integration
- **Frontend:** React with Context API
- **Storage:** HttpOnly cookies + localStorage (JWT)

## Database Schema

### Users Table
```sql
CREATE TABLE tripflow.users (
    id BIGSERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    email_verified BOOLEAN DEFAULT false,
    password_hash VARCHAR(255),  -- NULL for social login users
    full_name VARCHAR(255),
    avatar_url VARCHAR(500),

    -- OAuth fields
    google_id VARCHAR(255) UNIQUE,
    microsoft_id VARCHAR(255) UNIQUE,

    -- Subscription
    subscription_tier VARCHAR(50) DEFAULT 'free',
    trial_ends_at TIMESTAMP WITH TIME ZONE,

    -- Permissions
    is_active BOOLEAN DEFAULT true,
    is_admin BOOLEAN DEFAULT false,
    is_verified BOOLEAN DEFAULT false,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login_at TIMESTAMP WITH TIME ZONE
);

CREATE TABLE tripflow.user_sessions (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES tripflow.users(id) ON DELETE CASCADE,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    refresh_token VARCHAR(255),
    ip_address VARCHAR(45),
    user_agent VARCHAR(500),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE tripflow.oauth_connections (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES tripflow.users(id) ON DELETE CASCADE,
    provider VARCHAR(50) NOT NULL,  -- 'google', 'microsoft'
    provider_user_id VARCHAR(255) NOT NULL,
    access_token TEXT,
    refresh_token TEXT,
    token_expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(provider, provider_user_id)
);

CREATE INDEX idx_users_email ON tripflow.users(email);
CREATE INDEX idx_users_google ON tripflow.users(google_id) WHERE google_id IS NOT NULL;
CREATE INDEX idx_users_microsoft ON tripflow.users(microsoft_id) WHERE microsoft_id IS NOT NULL;
CREATE INDEX idx_sessions_token ON tripflow.user_sessions(session_token);
CREATE INDEX idx_sessions_user ON tripflow.user_sessions(user_id);
CREATE INDEX idx_oauth_user ON tripflow.oauth_connections(user_id);
```

## Backend Implementation

### 1. Dependencies
```bash
pip install python-jose[cryptography] passlib[bcrypt] python-multipart authlib httpx
```

### 2. Models
**`backend/app/models/user.py`**
- User model
- UserSession model
- OAuthConnection model

### 3. Auth Utilities
**`backend/app/core/security.py`**
```python
- create_access_token(user_id)
- verify_token(token)
- hash_password(password)
- verify_password(plain, hashed)
- generate_session_token()
```

### 4. OAuth Service
**`backend/app/services/oauth_service.py`**
```python
class OAuthService:
    - get_google_oauth_url()
    - verify_google_token(code)
    - get_microsoft_oauth_url()
    - verify_microsoft_token(code)
    - create_or_update_user(provider, user_info)
```

### 5. Auth API Endpoints
**`backend/app/api/auth.py`**
```
POST   /auth/register                  - Email/password signup
POST   /auth/login                     - Email/password login
POST   /auth/logout                    - Logout (invalidate session)
GET    /auth/me                        - Get current user
POST   /auth/refresh                   - Refresh JWT token

GET    /auth/google                    - Redirect to Google OAuth
GET    /auth/google/callback           - Handle Google callback
GET    /auth/microsoft                 - Redirect to Microsoft OAuth
GET    /auth/microsoft/callback        - Handle Microsoft callback

POST   /auth/verify-email              - Send verification email
GET    /auth/verify/{token}            - Verify email token
POST   /auth/forgot-password           - Send password reset
POST   /auth/reset-password            - Reset with token
```

### 6. Protected Routes
**Dependency injection pattern:**
```python
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    # Verify JWT and return user

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    if not current_user.is_active:
        raise HTTPException(403)
    return current_user

async def get_current_admin_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    if not current_user.is_admin:
        raise HTTPException(403)
    return current_user
```

### 7. Configuration
**`.env` additions:**
```env
# JWT
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Google OAuth
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8001/api/v1/auth/google/callback

# Microsoft OAuth
MICROSOFT_CLIENT_ID=your-microsoft-client-id
MICROSOFT_CLIENT_SECRET=your-microsoft-client-secret
MICROSOFT_REDIRECT_URI=http://localhost:8001/api/v1/auth/microsoft/callback
MICROSOFT_TENANT_ID=common

# Frontend URL
FRONTEND_URL=http://localhost:3000
```

## Frontend Implementation

### 1. Dependencies
```bash
npm install jwt-decode @react-oauth/google @azure/msal-browser
```

### 2. Auth Context
**`frontend/src/context/AuthContext.jsx`**
```jsx
const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [token, setToken] = useState(null);

  useEffect(() => {
    // Load token from localStorage
    // Verify token with backend
    // Load user data
  }, []);

  const login = async (email, password) => {
    // Call /auth/login
    // Store token
    // Load user
  };

  const loginWithGoogle = async (credentialResponse) => {
    // Send Google token to backend
    // Store JWT
    // Load user
  };

  const loginWithMicrosoft = async () => {
    // Initiate Microsoft OAuth flow
  };

  const logout = async () => {
    // Call /auth/logout
    // Clear token
    // Clear user
  };

  const register = async (email, password, fullName) => {
    // Call /auth/register
  };

  return (
    <AuthContext.Provider value={{
      user,
      token,
      loading,
      login,
      loginWithGoogle,
      loginWithMicrosoft,
      logout,
      register,
      isAuthenticated: !!user
    }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
```

### 3. Login Page
**`frontend/src/pages/Login.jsx`**

**Features:**
- Email/password form
- Google OAuth button
- Microsoft OAuth button
- "Forgot password" link
- "Sign up" link
- Redirect to intended page after login

**Components:**
```jsx
<LoginPage>
  <LoginForm />
  <GoogleLoginButton />
  <MicrosoftLoginButton />
  <Divider text="OR" />
  <EmailPasswordForm />
  <ForgotPasswordLink />
  <SignUpLink />
</LoginPage>
```

### 4. Signup Page
**`frontend/src/pages/Signup.jsx`**

**Features:**
- Full name input
- Email input
- Password input (with strength indicator)
- Terms & conditions checkbox
- Social signup buttons
- Already have account link

### 5. Protected Routes
**`frontend/src/components/ProtectedRoute.jsx`**
```jsx
const ProtectedRoute = ({ children, requireAdmin = false }) => {
  const { user, loading } = useAuth();

  if (loading) return <LoadingSpinner />;

  if (!user) {
    return <Navigate to="/login" state={{ from: location }} />;
  }

  if (requireAdmin && !user.is_admin) {
    return <Navigate to="/" />;
  }

  return children;
};
```

### 6. User Profile Dropdown
**`frontend/src/components/UserProfileDropdown.jsx`**

**Features:**
- User avatar
- Name and email
- "Profile" link
- "Settings" link
- "Logout" button
- Admin dashboard link (if admin)

### 7. Update App Routing
**`frontend/src/App.jsx`**
```jsx
<AuthProvider>
  <Routes>
    {/* Public routes */}
    <Route path="/login" element={<Login />} />
    <Route path="/signup" element={<Signup />} />
    <Route path="/forgot-password" element={<ForgotPassword />} />

    {/* Public trip planning (allow anonymous) */}
    <Route path="/" element={<TripFlowWizard />} />

    {/* Protected routes */}
    <Route path="/profile" element={
      <ProtectedRoute>
        <UserProfile />
      </ProtectedRoute>
    } />

    <Route path="/my-trips" element={
      <ProtectedRoute>
        <MyTrips />
      </ProtectedRoute>
    } />

    {/* Admin routes */}
    <Route path="/admin/*" element={
      <ProtectedRoute requireAdmin>
        <AdminLayout />
      </ProtectedRoute>
    } />
  </Routes>
</AuthProvider>
```

### 8. API Service Updates
**`frontend/src/services/api.js`**
```javascript
// Add request interceptor
axios.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  }
);

// Add response interceptor for 401 handling
axios.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Try to refresh token
      // If refresh fails, redirect to login
    }
    return Promise.reject(error);
  }
);
```

## Google OAuth Setup

### 1. Create Google Cloud Project
1. Go to https://console.cloud.google.com/
2. Create new project "TripFlow"
3. Enable Google+ API

### 2. Create OAuth Credentials
1. Go to Credentials
2. Create OAuth 2.0 Client ID
3. Application type: Web application
4. Authorized redirect URIs:
   - `http://localhost:8001/api/v1/auth/google/callback`
   - `http://localhost:3000/auth/google/callback` (for frontend)

### 3. Get Credentials
- Copy Client ID
- Copy Client Secret
- Add to `.env`

## Microsoft OAuth Setup

### 1. Register App in Azure
1. Go to https://portal.azure.com/
2. Azure Active Directory → App registrations
3. New registration: "TripFlow"

### 2. Configure Authentication
1. Add platform: Web
2. Redirect URIs:
   - `http://localhost:8001/api/v1/auth/microsoft/callback`
   - `http://localhost:3000/auth/microsoft/callback`
3. Enable ID tokens

### 3. API Permissions
- Add: Microsoft Graph → User.Read
- Grant admin consent

### 4. Get Credentials
- Copy Application (client) ID
- Create client secret
- Add to `.env`

## Security Considerations

### 1. Password Security
- Minimum 8 characters
- Hash with bcrypt (12 rounds)
- Rate limit login attempts
- Password strength indicator

### 2. JWT Security
- Short expiration (30 minutes)
- Refresh token rotation
- HttpOnly cookies for sensitive tokens
- CSRF protection

### 3. OAuth Security
- State parameter to prevent CSRF
- Verify tokens with provider
- Don't store OAuth access tokens long-term
- Use PKCE for public clients

### 4. Session Security
- Track active sessions per user
- Allow users to revoke sessions
- Automatic cleanup of expired sessions
- IP and user-agent logging

### 5. Email Verification
- Send verification email on signup
- Require verification for sensitive actions
- Expiring verification tokens

## Testing Plan

### Backend Tests
```python
# test_auth.py
def test_register_user()
def test_login_valid_credentials()
def test_login_invalid_credentials()
def test_google_oauth_callback()
def test_microsoft_oauth_callback()
def test_jwt_token_validation()
def test_protected_endpoint_requires_auth()
def test_refresh_token()
```

### Frontend Tests
```javascript
// AuthContext.test.js
test('login with email/password')
test('login with Google')
test('login with Microsoft')
test('logout')
test('protected route redirects when not authenticated')
```

## Implementation Steps

### Phase 1: Backend Core
1. ✅ Create user models
2. ✅ Create security utilities (JWT, password hashing)
3. ✅ Create basic auth endpoints (register, login, logout)
4. ✅ Add protected route dependencies
5. ✅ Test with Postman/curl

### Phase 2: Social Login Backend
6. ✅ Setup Google OAuth
7. ✅ Setup Microsoft OAuth
8. ✅ Create OAuth endpoints
9. ✅ Test OAuth flow

### Phase 3: Frontend Core
10. ✅ Create AuthContext
11. ✅ Create Login page
12. ✅ Create Signup page
13. ✅ Add ProtectedRoute component
14. ✅ Update routing

### Phase 4: Frontend Social Login
15. ✅ Add Google login button
16. ✅ Add Microsoft login button
17. ✅ Handle OAuth redirects
18. ✅ Test full flow

### Phase 5: UX Polish
19. ✅ Add user profile dropdown
20. ✅ Add loading states
21. ✅ Add error handling
22. ✅ Add success messages
23. ✅ Add password reset flow
24. ✅ Add email verification

## Success Metrics

- ✅ Users can register with email/password
- ✅ Users can login with email/password
- ✅ Users can login with Google
- ✅ Users can login with Microsoft
- ✅ JWT tokens are properly validated
- ✅ Protected routes require authentication
- ✅ Admin routes require admin role
- ✅ Sessions are properly managed
- ✅ OAuth tokens are securely handled

---

**Next:** Start with Phase 1 - Backend Core implementation
