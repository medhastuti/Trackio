CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY,
  name TEXT,
  email TEXT,
  password TEXT,
  role TEXT
);

CREATE TABLE IF NOT EXISTS complaints (
  id INTEGER PRIMARY KEY,
  title TEXT,
  description TEXT,
  status TEXT,
  user_id INTEGER,
  assigned_to INTEGER,
  rating INTEGER,
  feedback TEXT
);