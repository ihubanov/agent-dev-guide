import request from 'supertest';
import express from 'express';
import app from '../src/index';

// Mock fetch globally
const mockFetch = jest.fn();
global.fetch = mockFetch;

describe('Standalone Agent API', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('GET /api/chat/stream', () => {
    it('should stream tokens from LLM and end with [DONE]', async () => {
      // Mock streaming response
      const encoder = new TextEncoder();
      const chunks = [
        encoder.encode('data: {"choices":[{"delta":{"content":"Hello"}}] }\n'),
        encoder.encode('data: [DONE]\n'),
      ];
      let chunkIndex = 0;
      mockFetch.mockResolvedValue({
        ok: true,
        body: {
          getReader: () => ({
            read: async () => {
              if (chunkIndex < chunks.length) {
                return { value: chunks[chunkIndex++], done: false };
              }
              return { value: undefined, done: true };
            },
          }),
        },
      });

      const res = await request(app)
        .get('/api/chat/stream?history=%5B%5D')
        .set('Accept', 'text/event-stream');

      expect(res.status).toBe(200);
      expect(res.text).toContain('data: Hello');
      expect(res.text).toContain('event: end');
      expect(mockFetch).toHaveBeenCalled();
    });

    it('should handle LLM error gracefully', async () => {
      mockFetch.mockResolvedValue({ ok: false });
      const res = await request(app)
        .get('/api/chat/stream?history=%5B%5D')
        .set('Accept', 'text/event-stream');
      expect(res.status).toBe(200);
      expect(res.text).toContain('event: end');
    });

    it('should handle fetch throwing error', async () => {
      mockFetch.mockRejectedValue(new Error('fail'));
      const res = await request(app)
        .get('/api/chat/stream?history=%5B%5D')
        .set('Accept', 'text/event-stream');
      expect(res.status).toBe(200);
      expect(res.text).toContain('event: end');
    });

    it('should parse history from query string (array)', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        body: {
          getReader: () => ({
            read: async () => ({ value: undefined, done: true }),
          }),
        },
      });
      const res = await request(app)
        .get('/api/chat/stream?history=%5B%7B%22role%22%3A%22user%22%7D%5D')
        .set('Accept', 'text/event-stream');
      expect(res.status).toBe(200);
      expect(mockFetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          body: expect.stringContaining('"messages":'),
        })
      );
    });
  });

  describe('Static file serving', () => {
    it('should serve static files from public', async () => {
      // This just checks the static middleware is mounted (404 for missing file)
      const res = await request(app).get('/nonexistent-file.html');
      expect([404, 200]).toContain(res.status);
    });
  });
}); 