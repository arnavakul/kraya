import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter, Navigate, Route, Routes, useLocation, useNavigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './auth/AuthProvider';
import RequireAuth from './auth/RequireAuth';
import AppLayout from './components/AppLayout';
import Login from './Login';
import Signup from './Signup';
import RequestList from './pages/RequestList';
import RequestForm from './pages/RequestForm';
import RequestDetail from './pages/RequestDetail';
import './styles/requests.css';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      refetchOnWindowFocus: false,
      // Retrying a 4xx never helps; retry flaky network/server errors twice.
      retry: (failureCount, error) => !(error?.status >= 400 && error?.status < 500) && failureCount < 2,
    },
  },
});

function LoginRoute() {
  const { status, login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const from = location.state?.from?.pathname || '/requests';

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

  if (status === 'authed') return <Navigate to="/requests" replace />;

  return (
    <Signup
      onSignup={async (data) => {
        await register(data);
        navigate('/requests', { replace: true });
      }}
      onBack={() => navigate('/login')}
    />
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AuthProvider>
          <Routes>
            <Route path="/login" element={<LoginRoute />} />
            <Route path="/signup" element={<SignupRoute />} />

            <Route element={<RequireAuth />}>
              <Route element={<AppLayout />}>
                <Route index element={<Navigate to="/requests" replace />} />
                <Route path="requests" element={<RequestList />} />
                <Route path="requests/new" element={<RequestForm />} />
                <Route path="requests/:id" element={<RequestDetail />} />
                <Route path="requests/:id/edit" element={<RequestForm />} />
              </Route>
            </Route>

            <Route path="*" element={<Navigate to="/requests" replace />} />
          </Routes>
        </AuthProvider>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
