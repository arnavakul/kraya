import { BrowserRouter, Navigate, Route, Routes, useLocation, useNavigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './auth/AuthProvider';
import RequireAuth from './auth/RequireAuth';
import Login from './Login';
import Signup from './Signup';
import KrayaDashboard from './KrayaDashboard';

function LoginRoute() {
  const { status, login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const from = location.state?.from?.pathname || '/';

  if (status === 'authed') return <Navigate to={from} replace />;

  return (
    <Login
      onLogin={async (email, password) => {
        await login(email.trim(), password);
        navigate(from, { replace: true });
      }}
      onBack={() => navigate('/login')}
      onSignupClick={() => navigate('/signup')}
    />
  );
}

function SignupRoute() {
  const { status, register } = useAuth();
  const navigate = useNavigate();

  if (status === 'authed') return <Navigate to="/" replace />;

  return (
    <Signup
      onSignup={async (data) => {
        await register(data);
        navigate('/', { replace: true });
      }}
      onBack={() => navigate('/login')}
    />
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<LoginRoute />} />
          <Route path="/signup" element={<SignupRoute />} />
          <Route element={<RequireAuth />}>
            <Route path="/" element={<KrayaDashboard />} />
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}