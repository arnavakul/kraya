import assert from 'node:assert/strict';
import test from 'node:test';
import { ApiError, api, login } from '../src/lib/api.js';

test('authenticated workflow APIs send bearer tokens, refresh on 401, and parse results/errors', async () => {
  const previousFetch = globalThis.fetch;
  const calls = [];
  let latestAttempts = 0;
  globalThis.fetch = async (url, options) => {
    calls.push({ url, options });
    if (url.endsWith('/auth/login')) {
      return Response.json({ token: 'access-old', userId: 'u1' });
    }
    if (url.endsWith('/auth/refresh')) {
      return Response.json({ token: 'access-new' });
    }
    if (url.endsWith('/agent-workflows') && options.method === 'POST') {
      return Response.json({ runId: 'r1', workflow_status: 'supplier_review_required' });
    }
    if (url.endsWith('/agent-workflows/latest') && latestAttempts++ === 0) {
      return new Response(JSON.stringify({ message: 'expired' }), { status: 401 });
    }
    if (url.endsWith('/agent-workflows/latest')) {
      return Response.json({ runId: 'r1', workflow_status: 'supplier_review_required' });
    }
    return Response.json({ message: 'Agent unavailable' }, { status: 503 });
  };

  try {
    await login('synthetic@example.invalid', 'test-only-password');
    const run = await api('/requests/q1/agent-workflows', { method: 'POST' });
    assert.equal(run.runId, 'r1');
    assert.equal(calls.at(-1).options.headers.Authorization, 'Bearer access-old');

    const latest = await api('/requests/q1/agent-workflows/latest');
    assert.equal(latest.workflow_status, 'supplier_review_required');
    assert.equal(latestAttempts, 2);
    assert.equal(calls.at(-1).options.headers.Authorization, 'Bearer access-new');
    assert.equal(calls.at(-2).url, '/api/v1/auth/refresh');
    assert.equal(calls.at(-2).options.credentials, 'include');

    await assert.rejects(api('/requests/q1/fail'), (error) => {
      assert.ok(error instanceof ApiError);
      assert.equal(error.status, 503);
      assert.equal(error.message, 'Agent unavailable');
      return true;
    });
  } finally {
    globalThis.fetch = previousFetch;
  }
});
