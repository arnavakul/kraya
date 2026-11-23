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
import Dashboard from './pages/Dashboard';
import SupplierList from './pages/SupplierList';
import SupplierForm from './pages/SupplierForm';
import SupplierDetail from './pages/SupplierDetail';
import AgentChat from './pages/AgentChat';
import Analytics from './pages/Analytics';
import { AgentChatProvider } from './context/AgentChatContext';
import './styles/requests.css';
import './styles/suppliers.css';

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
          <AgentChatProvider>
            <Routes>
              <Route path="/login" element={<LoginRoute />} />
              <Route path="/signup" element={<SignupRoute />} />

              <Route element={<RequireAuth />}>
                <Route element={<AppLayout />}>
                  <Route index element={<Navigate to="/dashboard" replace />} />

                  <Route path="dashboard" element={<Dashboard />} />
                  <Route path="requests" element={<RequestList />} />
                  <Route path="requests/new" element={<RequestForm />} />
                  <Route path="requests/:id" element={<RequestDetail />} />
                  <Route path="requests/:id/edit" element={<RequestForm />} />

                  <Route path="suppliers" element={<SupplierList />} />
                  <Route path="suppliers/new" element={<SupplierForm />} />
                  <Route path="suppliers/:id" element={<SupplierDetail />} />
                  <Route path="suppliers/:id/edit" element={<SupplierForm />} />

                  <Route path="agents" element={<AgentChat />} />
                  <Route path="analytics" element={<Analytics />} />
                </Route>
              </Route>

              <Route path="*" element={<Navigate to="/requests" replace />} />
            </Routes>
          </AgentChatProvider>
        </AuthProvider>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
