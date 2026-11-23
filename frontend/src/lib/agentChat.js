import { useMutation } from '@tanstack/react-query';
import { api } from './api';

export function useSendChatMessage() {
  return useMutation({
    mutationFn: ({ message, conversationId }) =>
      api('/agent/chat', {
        method: 'POST',
        body: { message, conversationId: conversationId ?? null },
      }),
  });
}
