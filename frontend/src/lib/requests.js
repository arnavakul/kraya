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


export function useRunAgentWorkflow(id) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload) => api(`/requests/${id}/agent-workflows`, { method: 'POST', body: payload }),
    onSuccess: (data) => {
      queryClient.setQueryData(['requests', 'agent-workflow', id], data);
      queryClient.invalidateQueries({ queryKey: ['requests', 'agent-workflow', id] });
      queryClient.invalidateQueries({ queryKey: requestKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: requestKeys.audit(id) });
      queryClient.invalidateQueries({ queryKey: requestKeys.lists });
    },
  });
}

export function useLatestAgentWorkflow(id) {
  return useQuery({
    queryKey: ['requests', 'agent-workflow', id],
    queryFn: () => api(`/requests/${id}/agent-workflows/latest`),
    enabled: Boolean(id),
    retry: false,
  });
}

export function useApproveAndDispatchRfq(id) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload) => api(`/requests/${id}/agent-workflows/approve-rfq`, { method: 'POST', body: payload }),
    onSuccess: (data) => {
      queryClient.setQueryData(['requests', 'agent-workflow', id], data);
      queryClient.invalidateQueries({ queryKey: ['requests', 'agent-workflow', id] });
      queryClient.invalidateQueries({ queryKey: requestKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: requestKeys.audit(id) });
      queryClient.invalidateQueries({ queryKey: requestKeys.lists });
    },
  });
}

export function useSendThreadMessage(id) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload) => api(`/requests/${id}/agent-workflows/thread/message`, { method: 'POST', body: payload }),
    onSuccess: (data) => {
      queryClient.setQueryData(['requests', 'agent-workflow', id], data);
      queryClient.invalidateQueries({ queryKey: ['requests', 'agent-workflow', id] });
      queryClient.invalidateQueries({ queryKey: requestKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: requestKeys.audit(id) });
      queryClient.invalidateQueries({ queryKey: requestKeys.lists });
    },
  });
}

export function useApproveThreadDraft(id) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload) => api(`/requests/${id}/agent-workflows/thread/approve-draft`, { method: 'POST', body: payload }),
    onSuccess: (data) => {
      queryClient.setQueryData(['requests', 'agent-workflow', id], data);
      queryClient.invalidateQueries({ queryKey: ['requests', 'agent-workflow', id] });
      queryClient.invalidateQueries({ queryKey: requestKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: requestKeys.audit(id) });
      queryClient.invalidateQueries({ queryKey: requestKeys.lists });
    },
  });
}

export function useDiscardThreadDraft(id) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => api(`/requests/${id}/agent-workflows/thread/discard-draft`, { method: 'POST' }),
    onSuccess: (data) => {
      queryClient.setQueryData(['requests', 'agent-workflow', id], data);
      queryClient.invalidateQueries({ queryKey: ['requests', 'agent-workflow', id] });
      queryClient.invalidateQueries({ queryKey: requestKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: requestKeys.audit(id) });
      queryClient.invalidateQueries({ queryKey: requestKeys.lists });
    },
  });
}

export function useSyncWorkflowStatus(id) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => api(`/requests/${id}/agent-workflows/sync-status`, { method: 'POST' }),
    onSuccess: (data) => {
      queryClient.setQueryData(['requests', 'agent-workflow', id], data);
      queryClient.invalidateQueries({ queryKey: ['requests', 'agent-workflow', id] });
      queryClient.invalidateQueries({ queryKey: requestKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: requestKeys.audit(id) });
      queryClient.invalidateQueries({ queryKey: requestKeys.lists });
    },
  });
}

export function usePollInboxAndProcess(id) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload) =>
      fetch('/agent-api/inbox/poll-and-process', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          procurement_request_id: id,
          ...payload,
        }),
      }).then(async (res) => {
        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(err.detail || 'Inbox polling failed');
        }
        return res.json();
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['requests', 'agent-workflow', id] });
      queryClient.invalidateQueries({ queryKey: requestKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: requestKeys.audit(id) });
      queryClient.invalidateQueries({ queryKey: requestKeys.lists });
    },
  });
}

export function useGmailStatus() {
  return useQuery({
    queryKey: ['gmail', 'status'],
    queryFn: () =>
      fetch('/agent-api/inbox/gmail-status').then((res) => {
        if (!res.ok) throw new Error('Failed to fetch Gmail status');
        return res.json();
      }),
    refetchOnWindowFocus: false,
  });
}

export function useConfigureGmail() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload) =>
      fetch('/agent-api/inbox/configure-gmail', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      }).then(async (res) => {
        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(err.detail || 'Failed to configure Gmail');
        }
        return res.json();
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['gmail', 'status'] });
    },
  });
}
