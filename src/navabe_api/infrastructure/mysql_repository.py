
import json
import secrets
import string
from contextlib import contextmanager
from decimal import Decimal

import mysql.connector
from mysql.connector import IntegrityError

from navabe_api.domain.exceptions import ConflictError
from navabe_api.domain.models import Admin, Book, Order, OrderLine, User


class MySqlRepository:
    def __init__(self, config: dict):
        self.config = config

    @contextmanager
    def _cursor(self, commit: bool = False):
        connection = mysql.connector.connect(**self.config)
        cursor = connection.cursor(dictionary=True)
        try:
            yield cursor
            if commit:
                connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            cursor.close()
            connection.close()

    @staticmethod
    def _book(row: dict) -> Book:
        return Book(
            isbn=row["isbn"],
            title=row["titre"],
            author=row["auteur"],
            editor=row.get("editeur") or "",
            category=row.get("categorie") or "",
            synopsis=row.get("synopsis") or "",
            publication_year=row.get("annee_parution"),
            price=Decimal(str(row["prix"])),
            image_url=row.get("image_URL") or "",
            quantity=row.get("quantite"),
        )

    def _book_filter(self, query: str) -> tuple[str, list]:
        if not query:
            return "", []
        like = f"%{query}%"
        return (
            " WHERE l.isbn = %s OR l.titre LIKE %s OR l.auteur LIKE %s OR l.categorie LIKE %s",
            [query, like, like, like],
        )

    def list_books(self, query: str, limit: int, offset: int, sort: str, direction: str) -> list[Book]:
        sql = """
            SELECT l.*, i.quantite
            FROM Livres l LEFT JOIN Inventaire i ON i.isbn = l.isbn
        """
        where, params = self._book_filter(query)
        sql += where
        columns = {"title": "l.titre", "price": "l.prix", "publication_year": "l.annee_parution"}
        direction_sql = "DESC" if direction == "desc" else "ASC"
        if sort == "publication_year":
            sql += f" ORDER BY l.annee_parution IS NULL ASC, {columns[sort]} {direction_sql}, l.titre ASC, l.isbn ASC"
        else:
            sql += f" ORDER BY {columns[sort]} {direction_sql}, l.titre ASC, l.isbn ASC"
        sql += " LIMIT %s OFFSET %s"
        params.extend((limit, offset))
        with self._cursor() as cursor:
            cursor.execute(sql, params)
            return [self._book(row) for row in cursor.fetchall()]

    def count_books(self, query: str) -> int:
        where, params = self._book_filter(query)
        with self._cursor() as cursor:
            cursor.execute(f"SELECT COUNT(*) total FROM Livres l{where}", params)
            return int(cursor.fetchone()["total"])

    def get_book(self, isbn: str) -> Book | None:
        with self._cursor() as cursor:
            cursor.execute(
                "SELECT l.*, i.quantite FROM Livres l LEFT JOIN Inventaire i ON i.isbn=l.isbn WHERE l.isbn=%s",
                (isbn,),
            )
            row = cursor.fetchone()
            return self._book(row) if row else None

    def stock_available(self, isbn: str, quantity: int) -> bool:
        with self._cursor() as cursor:
            cursor.execute("SELECT quantite FROM Inventaire WHERE isbn=%s", (isbn,))
            row = cursor.fetchone()
            return bool(row and row["quantite"] >= quantity)

    def create_user(self, name: str, first_name: str, address: str, email: str, password_hash: str) -> User:
        try:
            with self._cursor(commit=True) as cursor:
                cursor.execute(
                    "INSERT INTO Clients(nom, prenom, adresse, mail, mot_de_passe) VALUES (%s,%s,%s,%s,%s)",
                    (name, first_name, address, email, password_hash),
                )
                cursor.execute("SELECT idClient FROM Clients WHERE mail=%s", (email,))
                identifier = cursor.fetchone()["idClient"]
        except IntegrityError as error:
            raise ConflictError("Email already registered", "email_exists") from error
        return User(identifier, name, first_name, address, email)

    def get_user_by_email(self, email: str) -> tuple[User, str] | None:
        with self._cursor() as cursor:
            cursor.execute(
                "SELECT idClient, nom, prenom, adresse, mail, mot_de_passe FROM Clients WHERE mail=%s",
                (email,),
            )
            row = cursor.fetchone()
            return self._user_record(row) if row else None

    def get_user_by_id(self, identifier: str) -> tuple[User, str] | None:
        with self._cursor() as cursor:
            cursor.execute(
                "SELECT idClient, nom, prenom, adresse, mail, mot_de_passe FROM Clients WHERE idClient=%s",
                (identifier,),
            )
            row = cursor.fetchone()
            return self._user_record(row) if row else None

    @staticmethod
    def _user_record(row: dict) -> tuple[User, str]:
        return User(row["idClient"], row["nom"], row["prenom"], row["adresse"], row["mail"]), row["mot_de_passe"]

    def update_user_password(self, identifier: str, password_hash: str) -> bool:
        with self._cursor(commit=True) as cursor:
            cursor.execute("UPDATE Clients SET mot_de_passe=%s WHERE idClient=%s", (password_hash, identifier))
            return cursor.rowcount == 1

    def create_order(self, user_id: str, transaction_id: str, lines: tuple[OrderLine, ...], amount: Decimal) -> Order:
        identifier = "".join((__import__("datetime").datetime.now().strftime("%Y%m%d"), secrets.token_hex(4).upper()))
        contents = {"isbn": [line.isbn for line in lines], "quantity": [line.quantity for line in lines]}
        with self._cursor(commit=True) as cursor:
            for line in lines:
                cursor.execute(
                    "UPDATE Inventaire SET quantite=quantite-%s WHERE isbn=%s AND quantite >= %s",
                    (line.quantity, line.isbn, line.quantity),
                )
                if cursor.rowcount != 1:
                    raise ConflictError(f"Insufficient stock for {line.isbn}", "insufficient_stock")
            cursor.execute(
                "INSERT INTO Commandes(idCommande,idClient,contenu) VALUES (%s,%s,%s)",
                (identifier, user_id, json.dumps(contents)),
            )
            cursor.execute(
                "INSERT INTO Paiements(idPaiement,idCommande,montant) VALUES (%s,%s,%s)",
                (transaction_id, identifier, amount),
            )
        return Order(identifier, user_id, transaction_id, amount, lines)

    def get_admin_by_id(self, identifier: str) -> tuple[Admin, str] | None:
        with self._cursor() as cursor:
            cursor.execute(
                """
                SELECT adminID, nom, prenom, mail, mot_de_passe, mot_de_passe_temporaire
                FROM Administrateur WHERE adminID=%s
                """,
                (identifier,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            return (
                Admin(
                    row["adminID"],
                    row["nom"],
                    row["prenom"],
                    row["mail"],
                    bool(row["mot_de_passe_temporaire"]),
                ),
                row["mot_de_passe"],
            )

    def create_admin(self, name: str, first_name: str, email: str, password_hash: str) -> Admin:
        identifier = (name[0] + first_name[0] + "".join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(4))).upper()
        try:
            with self._cursor(commit=True) as cursor:
                cursor.execute(
                    """
                    INSERT INTO Administrateur(adminID,nom,prenom,mail,mot_de_passe,mot_de_passe_temporaire)
                    VALUES (%s,%s,%s,%s,%s,TRUE)
                    """,
                    (identifier, name, first_name, email, password_hash),
                )
        except IntegrityError as error:
            raise ConflictError("Email already registered", "email_exists") from error
        return Admin(identifier, name, first_name, email, True)

    def update_admin_password(self, identifier: str, password_hash: str, temporary: bool = False) -> bool:
        with self._cursor(commit=True) as cursor:
            cursor.execute(
                """
                UPDATE Administrateur
                SET mot_de_passe=%s, mot_de_passe_temporaire=%s
                WHERE adminID=%s
                """,
                (password_hash, temporary, identifier),
            )
            return cursor.rowcount == 1

    def upsert_book(self, book: Book, quantity: int) -> Book:
        with self._cursor(commit=True) as cursor:
            cursor.execute(
                """
                INSERT INTO Livres(isbn,titre,auteur,editeur,categorie,synopsis,annee_parution,prix,image_URL)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON DUPLICATE KEY UPDATE titre=VALUES(titre), auteur=VALUES(auteur), editeur=VALUES(editeur),
                  categorie=VALUES(categorie), synopsis=VALUES(synopsis), annee_parution=VALUES(annee_parution),
                  prix=VALUES(prix), image_URL=VALUES(image_URL)
                """,
                (
                    book.isbn,
                    book.title,
                    book.author,
                    book.editor,
                    book.category,
                    book.synopsis,
                    book.publication_year,
                    book.price,
                    book.image_url,
                ),
            )
            cursor.execute(
                """
                INSERT INTO Inventaire(isbn,categorie,quantite) VALUES (%s,%s,%s)
                ON DUPLICATE KEY UPDATE categorie=VALUES(categorie), quantite=quantite+VALUES(quantite)
                """,
                (book.isbn, book.category, quantity),
            )
        return self.get_book(book.isbn) or book

    def delete_book(self, isbn: str) -> bool:
        with self._cursor(commit=True) as cursor:
            cursor.execute("DELETE FROM Inventaire WHERE isbn=%s", (isbn,))
            cursor.execute("DELETE FROM Livres WHERE isbn=%s", (isbn,))
            return cursor.rowcount == 1

    def get_order(self, identifier: str) -> dict | None:
        with self._cursor() as cursor:
            cursor.execute(
                """
                SELECT c.idCommande, c.idClient, c.contenu, c.date_commande, c.date_changement_etat, c.etat,
                       p.idPaiement, p.montant, p.date_Paiement, CONCAT(u.prenom, ' ', u.nom) customer
                FROM Commandes c JOIN Paiements p ON p.idCommande=c.idCommande
                JOIN Clients u ON u.idClient=c.idClient WHERE c.idCommande=%s
                """,
                (identifier,),
            )
            order = cursor.fetchone()
            if not order:
                return None
            contents = order["contenu"] if isinstance(order["contenu"], dict) else json.loads(order["contenu"])
            items = []
            for isbn, quantity in zip(contents["isbn"], contents["quantity"], strict=True):
                cursor.execute("SELECT titre,auteur,prix FROM Livres WHERE isbn=%s", (isbn,))
                book = cursor.fetchone()
                items.append(
                    {
                        "isbn": isbn,
                        "title_by_author": f"{book['titre']} by {book['auteur']}" if book else isbn,
                        "book_price": float(book["prix"]) if book else None,
                        "quantity": quantity,
                    }
                )
            return {
                "identifier": order["idCommande"],
                "user_id": order["idClient"],
                "customer": order["customer"],
                "transaction_id": order["idPaiement"],
                "amount": float(order["montant"]),
                "status": order["etat"],
                "created_at": order["date_commande"].isoformat(),
                "status_changed_at": order["date_changement_etat"].isoformat(),
                "paid_at": order["date_Paiement"].isoformat(),
                "items": items,
            }

    def statistics(self, metric: str, group_by: str) -> dict:
        queries = {
            ("stock", "category"): "SELECT categorie label, SUM(quantite) value FROM Inventaire GROUP BY categorie",
            ("stock", "year"): "SELECT annee_parution label, COUNT(*) value FROM Livres GROUP BY annee_parution",
            ("average-price", "category"): "SELECT categorie label, AVG(prix) value FROM Livres GROUP BY categorie",
            ("average-price", "year"): "SELECT annee_parution label, AVG(prix) value FROM Livres GROUP BY annee_parution",
            ("sales", ""): "SELECT DATE_FORMAT(date_Paiement,'%Y-%m') label, SUM(montant) value FROM Paiements GROUP BY label ORDER BY label",
            ("orders", ""): "SELECT etat label, COUNT(*) value FROM Commandes GROUP BY etat",
        }
        key = (metric, group_by or ("category" if metric in {"stock", "average-price"} else ""))
        sql = queries[key]
        with self._cursor() as cursor:
            cursor.execute(sql)
            rows = cursor.fetchall()
            return {"labels": [str(row["label"]) for row in rows], "values": [round(float(row["value"]), 2) for row in rows]}
