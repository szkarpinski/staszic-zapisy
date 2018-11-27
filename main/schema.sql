DROP TABLE IF EXISTS nauczyciele;
/*DROP TABLE IF EXISTS rodzice;*/
DROP TABLE IF EXISTS wizyty;

CREATE TABLE nauczyciele (
  id INTEGER PRIMARY KEY NOT NULL,
  imie TEXT NOT NULL,
  nazwisko TEXT NOT NULL,
  email TEXT NOT NULL,
  present INT NOT NULL DEFAULT 1
)

CREATE TABLE wizyty (
  id_nauczyciela INT NOT NULL,
  imie_rodzica TEXT NOT NULL,
  nazwisko_rodzica TEXT NOT NULL,
  email_rodzica TEXT NOT NULL,
  godzina TEXT NOT NULL
)
