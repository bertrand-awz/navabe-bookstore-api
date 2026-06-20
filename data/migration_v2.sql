USE NAVABE;

/* Required before writing Werkzeug password hashes and PayPal transaction IDs. */
ALTER TABLE Clients MODIFY mot_de_passe VARCHAR(255) NOT NULL;
ALTER TABLE Administrateur MODIFY mot_de_passe VARCHAR(255) NOT NULL;
ALTER TABLE Paiements MODIFY idPaiement VARCHAR(64) NOT NULL;
