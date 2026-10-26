import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from './api';

export const requestKeys = {
  lists: ['requests', 'list'],
  list: (params) => ['requests', 'list', params],
  detail: (id) => ['requests', 'detail', id],
  audit: (id) => ['requests', 'audit', id],
};

export function useRequests({ status, page, size = 20 }) {
  const params = new URLSearchParams({ page: String(page), size: String(size) });
  if (status) params.set('status', status);

  return useQuery({
    queryKey: requestKeys.list({ status: status || null, page, size }),
    queryFn: () => api(`/requests?${params}`),
    placeholderData: keepPreviousData, // keep the old page on screen while the next one loads
  });
}

export function useRequest(id) {
  return useQuery({
    queryKey: requestKeys.detail(id),
    queryFn: () => api(`/requests/${id}`),
    enabled: Boolean(id),
  });
}

export function useRequestAudit(id) {
  return useQuery({
    queryKey: requestKeys.audit(id),
    queryFn: () => api(`/requests/${id}/audit`),
    enabled: Boolean(id),
  });
}

function useAfterSave() {
  const queryClient = useQueryClient();
  return (saved) => {
    queryClient.setQueryData(requestKeys.detail(saved.id), saved);
    queryClient.invalidateQueries({ queryKey: requestKeys.lists });
    queryClient.invalidateQueries({ queryKey: requestKeys.audit(saved.id) });
  };
}

export function useCreateRequest() {
  const afterSave = useAfterSave();
  return useMutation({
    mutationFn: (payload) => api('/requests', { method: 'POST', body: payload }),
    onSuccess: afterSave,
  });
}

export function useUpdateRequest(id) {
  const afterSave = useAfterSave();
  return useMutation({
    mutationFn: (payload) => api(`/requests/${id}`, { method: 'PUT', body: payload }),
    onSuccess: afterSave,
  });
}

export function useTransition(id) {
  const afterSave = useAfterSave();
  return useMutation({
    mutationFn: ({ to, reason }) =>
      api(`/requests/${id}/transitions`, { method: 'POST', body: { to, reason: reason || null } }),
    onSuccess: afterSave,
  });
}