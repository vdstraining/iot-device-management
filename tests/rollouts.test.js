const request = require('supertest');
const app = require('../src/server');
const db = require('../src/db');

beforeAll(() => {
  process.env.NODE_ENV = 'test';
});

afterAll((done) => {
  db.close(done);
});

test('create -> get -> pause rollout', async () => {
  const due = new Date(Date.now() + 60000).toISOString();
  const createRes = await request(app).post('/rollouts').send({ payload: { hello: 'world' }, due_at: due });
  expect(createRes.statusCode).toBe(201);
  const id = createRes.body.id;
  expect(id).toBeGreaterThan(0);

  const getRes = await request(app).get(`/rollouts/${id}`);
  expect(getRes.statusCode).toBe(200);
  expect(getRes.body.state).toBe('scheduled');

  const pauseRes = await request(app).patch(`/rollouts/${id}/pause`).send();
  expect(pauseRes.statusCode).toBe(200);
  expect(pauseRes.body.state).toBe('paused');
});
