PRAGMA foreign_keys = ON;


CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    login TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE tracks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    title TEXT NOT NULL,
    author TEXT,
    album TEXT,

    genre TEXT,
    year INTEGER,
    duration INTEGER,
    bitrate INTEGER,
    format TEXT,

    file_path TEXT NOT NULL UNIQUE,
    cover_path TEXT,

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE playlists (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    owner_id INTEGER NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (owner_id)
        REFERENCES users(id)
        ON DELETE CASCADE
);


CREATE TABLE playlist_tracks (
    playlist_id INTEGER NOT NULL,
    track_id INTEGER NOT NULL,

    position INTEGER DEFAULT 0,
    PRIMARY KEY (playlist_id, track_id),
    FOREIGN KEY (playlist_id)
        REFERENCES playlists(id)
        ON DELETE CASCADE,
    FOREIGN KEY (track_id)
        REFERENCES tracks(id)
        ON DELETE CASCADE
);