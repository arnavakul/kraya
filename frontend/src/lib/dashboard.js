import { useQuery } from '@tanstack/react-query';
import { api } from './api';

export const dashboardKeys = {
  root: ['dashboard'],
};

export function useDashboard() {
  return useQuery({
    queryKey: dashboardKeys.root,
    queryFn: () => api('/dashboard'),
    staleTime: 30_000,
  });
}
