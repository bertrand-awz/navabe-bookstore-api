CREATE DATABASE IF NOT EXISTS NAVABE
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE NAVABE;

/* Create a least-privilege application user separately. Its credentials belong
   in backend/.env and must never be versioned. */

CREATE TABLE IF NOT EXISTS Administrateur (
  adminID CHAR(6) NOT NULL,
  nom VARCHAR(45) NOT NULL,
  prenom VARCHAR(45) NOT NULL,
  mail VARCHAR(255) NOT NULL,
  mot_de_passe VARCHAR(255) NOT NULL,
  PRIMARY KEY (adminID),
  UNIQUE KEY uq_administrateur_mail (mail)
);

CREATE TABLE IF NOT EXISTS Clients (
  numClient INT UNSIGNED ZEROFILL AUTO_INCREMENT,
  idClient CHAR(8) NOT NULL,
  nom VARCHAR(45) NOT NULL,
  prenom VARCHAR(45) NOT NULL,
  adresse VARCHAR(255) NOT NULL,
  mail VARCHAR(255) NOT NULL,
  mot_de_passe VARCHAR(255) NOT NULL,
  PRIMARY KEY (idClient),
  UNIQUE KEY uq_client_number (numClient),
  UNIQUE KEY uq_client_mail (mail)
);

CREATE TABLE IF NOT EXISTS Livres (
  isbn CHAR(13) NOT NULL,
  titre VARCHAR(1500) NOT NULL,
  auteur VARCHAR(1000) NOT NULL,
  editeur VARCHAR(1000),
  categorie VARCHAR(1000),
  synopsis VARCHAR(6000),
  annee_parution SMALLINT UNSIGNED,
  prix DECIMAL(10, 2) UNSIGNED NOT NULL,
  image_URL VARCHAR(3000),
  PRIMARY KEY (isbn),
  INDEX idx_livres_auteur (auteur(100)),
  INDEX idx_livres_titre (titre(100)),
  INDEX idx_livres_categorie (categorie(100))
);

CREATE TABLE IF NOT EXISTS Inventaire (
  isbn CHAR(13) NOT NULL,
  categorie VARCHAR(1000),
  quantite INT UNSIGNED NOT NULL DEFAULT 0,
  PRIMARY KEY (isbn),
  CONSTRAINT fk_inventaire_livre FOREIGN KEY (isbn) REFERENCES Livres(isbn) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS Commandes (
  idCommande CHAR(16) NOT NULL,
  idClient CHAR(8) NOT NULL,
  contenu JSON NOT NULL,
  date_commande DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  date_changement_etat DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  etat VARCHAR(30) NOT NULL DEFAULT 'In process',
  PRIMARY KEY (idCommande),
  CONSTRAINT fk_commande_client FOREIGN KEY (idClient) REFERENCES Clients(idClient)
);

CREATE TABLE IF NOT EXISTS Paiements (
  idPaiement VARCHAR(64) NOT NULL,
  date_Paiement DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  idCommande CHAR(16) NOT NULL,
  montant DECIMAL(10, 2) UNSIGNED NOT NULL,
  PRIMARY KEY (idPaiement),
  UNIQUE KEY uq_paiement_commande (idCommande),
  CONSTRAINT fk_paiement_commande FOREIGN KEY (idCommande) REFERENCES Commandes(idCommande)
);

CREATE TABLE IF NOT EXISTS schema_migrations (
  version VARCHAR(100) NOT NULL PRIMARY KEY,
  applied_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

DELIMITER //
CREATE TRIGGER id_clients_generator
BEFORE INSERT ON Clients
FOR EACH ROW
BEGIN
  DECLARE max_num INT;
  SELECT IFNULL(MAX(numClient), 0) INTO max_num FROM Clients;
  SET NEW.idClient = UPPER(CONCAT(SUBSTR(NEW.prenom, 1, 2), SUBSTR(NEW.nom, 1, 2), LPAD(max_num + 1, 4, '0')));
END//
DELIMITER ;

/* Import the supplied catalog after adapting the path to the MySQL server:
   LOAD DATA INFILE '/var/lib/mysql-files/NVB.csv'
   INTO TABLE Livres FIELDS TERMINATED BY '|' LINES TERMINATED BY '\n'
   IGNORE 1 ROWS;
*/
