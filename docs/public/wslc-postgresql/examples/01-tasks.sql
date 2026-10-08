-- psql 画面で実行。実データの DB に対して実行しないこと。
CREATE TABLE IF NOT EXISTS tasks (
  id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  title text NOT NULL UNIQUE,
  done boolean NOT NULL DEFAULT false
);
INSERT INTO tasks (title)
VALUES ('Start PostgreSQL'), ('Connect from my app')
ON CONFLICT (title) DO NOTHING;
SELECT id, title, done FROM tasks ORDER BY id;
UPDATE tasks SET done = true WHERE title = 'Start PostgreSQL';
INSERT INTO tasks (title)
VALUES ('My first container database')
ON CONFLICT (title) DO NOTHING;
SELECT title, done FROM tasks ORDER BY id;
SELECT count(*) FROM tasks;
