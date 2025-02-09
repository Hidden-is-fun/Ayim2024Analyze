"""
I've NEVER created a database by my own before, but piles of .json files seems too messy.
Start to learn at 3:20 AM Feb 8, 2025
"""

import sqlite3

conn = sqlite3.connect('statistics.db')
c = conn.cursor()
c.execute('''
CREATE TABLE IF NOT EXISTS BeatmapSet(
ID      INTEGER PRIMARY KEY AUTOINCREMENT,
SetID   INTEGER NOT NULL,
Host    INTEGER NOT NULL,
Artist  TEXT NOT NULL,
Title   TEXT NOT NULL,
Diffs   INTEGER NOT NULL,
RankedDate  DATETIME NOT NULL,
IsRanked    BOOLEAN NOT NULL,
VoteCount   INTEGER NOT NULL,
Rating  REAL NOT NULL
);''')
c.execute('''
CREATE TABLE IF NOT EXISTS Beatmap(
ID      INTEGER PRIMARY KEY AUTOINCREMENT,
SetID  INTEGER NOT NULL,
MapID  INTEGER NOT NULL,
GameMode    INTEGER NOT NULL,
KeyCount    INTEGER,
DiffName    TEXT NOT NULL,
SR      REAL NOT NULL,
Drain   INTEGER NOT NULL,
PassCount   INTEGER NOT NULL,
PlayCount   INTEGER NOT NULL,
UpdateTime  DATETIME NOT NULL
);''')
c.execute('''
CREATE TABLE IF NOT EXISTS DiffOwner(
ID      INTEGER PRIMARY KEY AUTOINCREMENT,
MapID   INTEGER NOT NULL,
UserID  INTEGER NOT NULL
);''')
c.execute('''
CREATE TABLE IF NOT EXISTS BN(
ID      INTEGER PRIMARY KEY AUTOINCREMENT,
SetID   INTEGER NOT NULL,
UserID  INTEGER NOT NULL
);''')
c.execute('''
CREATE TABLE IF NOT EXISTS User(
ID      INTEGER PRIMARY KEY AUTOINCREMENT,
UserID  INTEGER NOT NULL,
Username    TEXT,
Country     TEXT,
UpdateTime  DATETIME NOT NULL
);''')
c.execute('''
CREATE TABLE IF NOT EXISTS UserAlias(
ID      INTEGER PRIMARY KEY AUTOINCREMENT,
UserID  INTEGER NOT NULL,
PreviousUsername    TEXT NOT NULL
);''')
conn.commit()
conn.close()
