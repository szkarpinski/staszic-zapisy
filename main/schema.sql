DROP TABLE IF EXISTS nauczyciele;
DROP TABLE IF EXISTS rodzice;
DROP TABLE IF EXISTS wizyty;


CREATE TABLE nauczyciele (
  id INTEGER PRIMARY KEY NOT NULL,
  imie TEXT NOT NULL,
  nazwisko TEXT NOT NULL,
  email TEXT NOT NULL,
  obecny INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE rodzice (
  id INTEGER PRIMARY KEY NOT NULL,
  imie TEXT NOT NULL,
  nazwisko TEXT NOT NULL,
  email TEXT NOT NULL,
  imie_ucznia TEXT NOT NULL,
  nazwisko_ucznia TEXT NOT NULL
);

CREATE TABLE wizyty (
  id_nauczyciela INTEGER NOT NULL,
  id_rodzica INTEGER NOT NULL,
  godzina TEXT NOT NULL,
  FOREIGN KEY (id_nauczyciela) REFERENCES nauczyciele (id),
  FOREIGN KEY (id_rodzica) REFERENCES rodzice (id),
  PRIMARY KEY (id_nauczyciela, godzina)
);
