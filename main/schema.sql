DROP TABLE IF EXISTS nauczyciele;
/*DROP TABLE IF EXISTS rodzice;*/
DROP TABLE IF EXISTS wizyty;


CREATE TABLE nauczyciele (
  id INTEGER PRIMARY KEY NOT NULL AUTO INCREMENT,
  imie TEXT NOT NULL,
  nazwisko TEXT NOT NULL,
  email TEXT NOT NULL,
  obecny INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE wizyty (
  id_nauczyciela INTEGER NOT NULL,
  imie_rodzica TEXT NOT NULL,
  nazwisko_rodzica TEXT NOT NULL,
  email_rodzica TEXT NOT NULL,
  imie_ucznia TEXT NOT NULL,
  nazwisko_ucznia TEXT NOT NULL,
  godzina TEXT NOT NULL,
  FOREIGN KEY (id_nauczyciela) REFERENCES nauczyciele (id)
);
