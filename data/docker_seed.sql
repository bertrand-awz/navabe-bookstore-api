USE NAVABE;

LOAD DATA INFILE '/var/lib/mysql-files/NVB.csv'
IGNORE INTO TABLE Livres
FIELDS TERMINATED BY '|'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(isbn, titre, auteur, editeur, categorie, synopsis, annee_parution, prix, image_URL);

INSERT IGNORE INTO Inventaire (isbn, categorie, quantite)
SELECT isbn, categorie, 50
FROM Livres;

INSERT IGNORE INTO schema_migrations (version)
VALUES ('001_initial_schema');
