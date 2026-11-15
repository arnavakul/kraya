import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from './api';

export const SUPPLIER_STATUSES = ['ACTIVE', 'INACTIVE', 'BLOCKED'];

export const supplierKeys = {
  lists: ['suppliers', 'list'],
  list: (params) => ['suppliers', 'list', params],
  detail: (id) => ['suppliers', 'detail', id],
};

export function useSuppliers({ status, q, page, size = 20 }) {
  const params = new URLSearchParams({ page: String(page), size: String(size) });
  if (status) params.set('status', status);
  if (q) params.set('q', q);

  return useQuery({
    queryKey: supplierKeys.list({ status: status || null, q: q || null, page, size }),
    queryFn: () => api(`/suppliers?${params}`),
    placeholderData: keepPreviousData,
  });
}

export function useSupplier(id) {
  return useQuery({
    queryKey: supplierKeys.detail(id),
    queryFn: () => api(`/suppliers/${id}`),
    enabled: Boolean(id),
  });
}

function useAfterSave() {
  const queryClient = useQueryClient();
  return (saved) => {
    queryClient.setQueryData(supplierKeys.detail(saved.id), saved);
    queryClient.invalidateQueries({ queryKey: supplierKeys.lists });
  };
}

export function useCreateSupplier() {
  const afterSave = useAfterSave();
  return useMutation({
    mutationFn: (payload) => api('/suppliers', { method: 'POST', body: payload }),
    onSuccess: afterSave,
  });
}

export function useUpdateSupplier(id) {
  const afterSave = useAfterSave();
  return useMutation({
    mutationFn: (payload) => api(`/suppliers/${id}`, { method: 'PUT', body: payload }),
    onSuccess: afterSave,
  });
}

export function useSupplierStatus(id) {
  const afterSave = useAfterSave();
  return useMutation({
    mutationFn: ({ status, reason }) =>
      api(`/suppliers/${id}/status`, { method: 'POST', body: { status, reason: reason || null } }),
    onSuccess: afterSave,
  });
}