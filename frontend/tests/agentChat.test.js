import assert from 'node:assert/strict';
import test from 'node:test';
import { api, login } from '../src/lib/api.js';

test('agent chat API sends message, handles conversationId, and parses progress', async () => {
  const previousFetch = globalThis.fetch;
  const calls = [];

  globalThis.fetch = async (url, options) => {
    calls.push({ url, options });
    if (url.endsWith('/auth/login')) {
      return Response.json({ token: 'mock-jwt-token', userId: 'u1' });
    }
    if (url.endsWith('/agent/chat') && options.method === 'POST') {
      const body = JSON.parse(options.body);
      return Response.json({
        conversationId: body.conversationId || 'conv-12345',
        reply: "Got it! I'll handle the end-to-end procurement for you. Here's the plan:",
        steps: [
          { label: 'Extract and validate your requirements', status: 'done', done: true },
          { label: 'Discover and shortlist suitable suppliers', status: 'current', done: false },
        ],
        procurementProgress: {
          currentStage: 'Supplier Discovery',
          stages: ['Requirement Analysis', 'Supplier Discovery', 'Quote Collection'],
        },
      });
    }
    return Response.json({ message: 'Not found' }, { status: 404 });
  };

  try {
    await login('manager@example.com', 'secure-password');

    // First call without conversationId
    const res1 = await api('/agent/chat', {
      method: 'POST',
      body: { message: 'I need 20 laptops for my R&D team' },
    });

    assert.equal(res1.conversationId, 'conv-12345');
    assert.equal(res1.procurementProgress.currentStage, 'Supplier Discovery');
    assert.equal(res1.steps.length, 2);
    assert.equal(res1.steps[0].status, 'done');
    assert.equal(calls.at(-1).options.headers.Authorization, 'Bearer mock-jwt-token');

    // Second call threading conversationId
    const res2 = await api('/agent/chat', {
      method: 'POST',
      body: { message: "What's the current status?", conversationId: res1.conversationId },
    });

    assert.equal(res2.conversationId, 'conv-12345');
    const sentBody = JSON.parse(calls.at(-1).options.body);
    assert.equal(sentBody.conversationId, 'conv-12345');
  } finally {
    globalThis.fetch = previousFetch;
  }
});
