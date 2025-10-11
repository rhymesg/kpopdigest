import { Pool } from 'pg';

const connectionString = process.env.DATABASE_URL;

if (!connectionString) {
  throw new Error('DATABASE_URL is required to run the frontend.');
}

const globalForPool = global as unknown as { __kpop_pool?: Pool };

export const pool =
  globalForPool.__kpop_pool ??
  new Pool({
    connectionString,
    ssl: { rejectUnauthorized: false },
    max: 5,
  });

if (!globalForPool.__kpop_pool) {
  globalForPool.__kpop_pool = pool;
}
