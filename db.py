import os
import sqlite3
from pathlib import Path
from datetime import datetime, date, timedelta
from typing import List, Optional, Dict, Any, Tuple
from functools import lru_cache
import threading

APP_NAME = "PerspectiVo"


import os
from pathlib import Path

APP_NAME = "PerspectiVo"

def get_app_db_path() -> Path:
    # Windows: C:\Users\NomUtilisateur\Documents\PerspectiVo
    # macOS/Linux: ~/Documents/PerspectiVo
    documents = Path.home() / "Documents"
    
    if not documents.exists():
        documents = Path.home()  # Fallback si Documents n'existe pas
    
    app_folder = documents / APP_NAME
    app_folder.mkdir(parents=True, exist_ok=True)
    
    return app_folder / "perspectivo.db"


class DBManager:
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or get_app_db_path()
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def cursor(self):
        return self.conn.cursor()

    def commit(self):
        self.conn.commit()

    def _init_schema(self):
        cur = self.conn.cursor()
        # users (auth)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT,
            prenoms TEXT,
            email TEXT UNIQUE,
            password_hash TEXT,
            failed_attempts INTEGER DEFAULT 0,
            locked_until INTEGER DEFAULT 0,
            remember_token_hash TEXT
        );
        """)
        # members - CORRIGÉ: ajout de date_inscription
        cur.execute("""
        CREATE TABLE IF NOT EXISTS members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL,
            prenoms TEXT,
            contact TEXT,
            email TEXT,
            residence TEXT,
            ecole TEXT,
            filiere TEXT,
            date_inscription TEXT DEFAULT CURRENT_TIMESTAMP,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        """)
        # groups
        cur.execute("""
        CREATE TABLE IF NOT EXISTS groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL UNIQUE,
            description TEXT,
            couleur TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        """)
        # group_members
        cur.execute("""
        CREATE TABLE IF NOT EXISTS group_members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id INTEGER NOT NULL,
            member_id INTEGER NOT NULL,
            added_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(group_id, member_id),
            FOREIGN KEY(group_id) REFERENCES groups(id) ON DELETE CASCADE,
            FOREIGN KEY(member_id) REFERENCES members(id) ON DELETE CASCADE
        );
        """)
        # events - CORRIGÉ: renommé date_event en date
        cur.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL,
            date TEXT NOT NULL,
            heure TEXT,
            lieu TEXT,
            description TEXT,
            groupe_id INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(groupe_id) REFERENCES groups(id) ON DELETE SET NULL
        );
        """)
        # presences
        cur.execute("""
        CREATE TABLE IF NOT EXISTS presences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            member_id INTEGER NOT NULL,
            event_id INTEGER,
            date TEXT NOT NULL,
            present INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(member_id) REFERENCES members(id) ON DELETE CASCADE,
            FOREIGN KEY(event_id) REFERENCES events(id) ON DELETE SET NULL
        );
        """)
        # messages
        cur.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT,
            recipient TEXT,
            groupe_id INTEGER,
            content TEXT,
            sent_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        """)
        self.conn.commit()
    
    def clear_caches(self):
        """Efface tous les caches - appeler après modification"""
        for manager in getattr(self, '_managers', []):
            if hasattr(manager, '_cache_taux'):
                manager._cache_taux.clear()


class MembresManager:
    def __init__(self, db: DBManager):
        self.db = db
        self._cache_taux = {}  # Cache pour taux_presence

    def ajouter_membre(self, nom: str, prenoms: str = "", contact: str = "", residence: str = "",
                       email: str = "", ecole: str = "", filiere: str = "") -> int:
        cur = self.db.cursor()
        cur.execute("""
            INSERT INTO members (nom, prenoms, contact, email, residence, ecole, filiere, date_inscription)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (nom, prenoms, contact, email, residence, ecole, filiere, datetime.now().isoformat()))
        self.db.commit()
        self._cache_taux.clear()
        return cur.lastrowid

    def obtenir_tous_membres(self) -> List[Dict[str, Any]]:
        cur = self.db.cursor()
        cur.execute("SELECT * FROM members ORDER BY nom, prenoms")
        return [dict(r) for r in cur.fetchall()]

    def obtenir_membre(self, member_id: int) -> Optional[Dict[str, Any]]:
        cur = self.db.cursor()
        cur.execute("SELECT * FROM members WHERE id = ?", (member_id,))
        r = cur.fetchone()
        return dict(r) if r else None

    def supprimer_membre(self, member_id: int):
        cur = self.db.cursor()
        cur.execute("DELETE FROM members WHERE id = ?", (member_id,))
        self.db.commit()
        self._cache_taux.clear()

    def modifier_membre(self, member_id: int, **fields):
        if not fields:
            return
        keys = ", ".join(f"{k}=?" for k in fields.keys())
        vals = list(fields.values()) + [member_id]
        cur = self.db.cursor()
        cur.execute(f"UPDATE members SET {keys} WHERE id = ?", vals)
        self.db.commit()
        self._cache_taux.clear()

    def obtenir_membres_du_groupe(self, group_id: int) -> List[Dict[str, Any]]:
        cur = self.db.cursor()
        cur.execute("""
            SELECT m.* FROM members m
            JOIN group_members gm ON gm.member_id = m.id
            WHERE gm.group_id = ?
            ORDER BY m.nom, m.prenoms
        """, (group_id,))
        return [dict(r) for r in cur.fetchall()]

    def calculer_taux_presence(self, member_id: int) -> float:
        """Retourne le taux de présence avec cache"""
        if member_id in self._cache_taux:
            return self._cache_taux[member_id]
        
        cur = self.db.cursor()
        cur.execute("SELECT COUNT(*) FROM presences WHERE member_id = ?", (member_id,))
        total = cur.fetchone()[0] or 0
        
        if total == 0:
            result = 0.0
        else:
            cur.execute("SELECT COUNT(*) FROM presences WHERE member_id = ? AND present = 1", (member_id,))
            present = cur.fetchone()[0] or 0
            result = round((present / total) * 100, 2)
        
        self._cache_taux[member_id] = result
        return result


class GroupesManager:
    def __init__(self, db: DBManager):
        self.db = db

    def ajouter_groupe(self, nom: str, description: str = "", couleur: str = "") -> int:
        cur = self.db.cursor()
        cur.execute("INSERT INTO groups (nom, description, couleur) VALUES (?, ?, ?)", 
                   (nom, description, couleur))
        self.db.commit()
        return cur.lastrowid

    def obtenir_tous_groupes(self) -> List[Dict[str, Any]]:
        cur = self.db.cursor()
        cur.execute("SELECT * FROM groups ORDER BY nom")
        groupes = [dict(r) for r in cur.fetchall()]
        
        # CORRIGÉ: Ajouter le nombre de membres pour chaque groupe
        for g in groupes:
            cur.execute("SELECT COUNT(*) FROM group_members WHERE group_id = ?", (g['id'],))
            g['nombre_membres'] = cur.fetchone()[0] or 0
        
        return groupes

    def obtenir_groupe(self, group_id: int) -> Optional[Dict[str, Any]]:
        cur = self.db.cursor()
        cur.execute("SELECT * FROM groups WHERE id = ?", (group_id,))
        r = cur.fetchone()
        if not r:
            return None
        
        groupe = dict(r)
        cur.execute("SELECT COUNT(*) FROM group_members WHERE group_id = ?", (group_id,))
        groupe['nombre_membres'] = cur.fetchone()[0] or 0
        return groupe

    def ajouter_membre_au_groupe(self, group_id: int, member_id: int):
        """CORRIGÉ: paramètres dans le bon ordre"""
        cur = self.db.cursor()
        try:
            cur.execute("INSERT INTO group_members (group_id, member_id) VALUES (?, ?)", 
                       (group_id, member_id))
            self.db.commit()
        except sqlite3.IntegrityError:
            pass  # déjà membre

    def retirer_membre_du_groupe(self, group_id: int, member_id: int):
        cur = self.db.cursor()
        cur.execute("DELETE FROM group_members WHERE group_id = ? AND member_id = ?", 
                   (group_id, member_id))
        self.db.commit()

    def modifier_groupe(self, groupe_id: int, **fields):
        """CORRIGÉ: met à jour la table 'groups' pas 'members'"""
        if not fields:
            return
        keys = ", ".join(f"{k}=?" for k in fields.keys())
        vals = list(fields.values()) + [groupe_id]
        cur = self.db.cursor()
        cur.execute(f"UPDATE groups SET {keys} WHERE id = ?", vals)
        self.db.commit()
    
    def supprimer_groupe(self, group_id: int) -> bool:
        """CORRIGÉ: méthode manquante"""
        try:
            cur = self.db.cursor()
            cur.execute("DELETE FROM groups WHERE id = ?", (group_id,))
            self.db.commit()
            return True
        except Exception as e:
            print(f"Erreur suppression groupe: {e}")
            return False


class EvenementsManager:
    def __init__(self, db: DBManager):
        self.db = db

    def ajouter_evenement(self, nom: str, date_str: str, heure: str = "", lieu: str = "",
                         description: str = "", groupe_id: Optional[int] = None) -> int:
        cur = self.db.cursor()
        cur.execute("""
            INSERT INTO events (nom, date, heure, lieu, description, groupe_id)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (nom, date_str, heure, lieu, description, groupe_id))
        self.db.commit()
        return cur.lastrowid

    def obtenir_tous_evenements(self, futurs_seulement: bool = False) -> List[Dict[str, Any]]:
        cur = self.db.cursor()
        if futurs_seulement:
            today = date.today().isoformat()
            cur.execute("SELECT * FROM events WHERE date >= ? ORDER BY date, heure", (today,))
        else:
            cur.execute("SELECT * FROM events ORDER BY date DESC, heure DESC")
        return [dict(r) for r in cur.fetchall()]

    def obtenir_evenement(self, event_id: int) -> Optional[Dict[str, Any]]:
        cur = self.db.cursor()
        cur.execute("SELECT * FROM events WHERE id = ?", (event_id,))
        r = cur.fetchone()
        return dict(r) if r else None

    def supprimer_evenement(self, event_id: int):
        cur = self.db.cursor()
        cur.execute("DELETE FROM events WHERE id = ?", (event_id,))
        self.db.commit()


class PresencesManager:
    def __init__(self, db: DBManager):
        self.db = db

    def enregistrer_presence(self, member_id: int, event_id: Optional[int], present: bool, 
                           date_str: Optional[str] = None) -> int:
        date_str = date_str or date.today().isoformat()
        cur = self.db.cursor()
        cur.execute("""
            INSERT INTO presences (member_id, event_id, date, present)
            VALUES (?, ?, ?, ?)
        """, (member_id, event_id, date_str, 1 if present else 0))
        self.db.commit()
        return cur.lastrowid

    def obtenir_presences_pour_membre(self, member_id: int) -> List[Dict[str, Any]]:
        cur = self.db.cursor()
        cur.execute("SELECT * FROM presences WHERE member_id = ? ORDER BY date DESC", (member_id,))
        return [dict(r) for r in cur.fetchall()]

    def obtenir_presences_par_date(self, date_str: str) -> List[Dict[str, Any]]:
        cur = self.db.cursor()
        cur.execute("SELECT * FROM presences WHERE date = ?", (date_str,))
        return [dict(r) for r in cur.fetchall()]
    
    def obtenir_presences_evenement(self, event_id: int) -> List[Dict[str, Any]]:
        """CORRIGÉ: méthode manquante"""
        cur = self.db.cursor()
        cur.execute("SELECT * FROM presences WHERE event_id = ? ORDER BY date DESC", (event_id,))
        return [dict(r) for r in cur.fetchall()]


class MessagesManager:
    def __init__(self, db: DBManager):
        self.db = db

    def enregistrer_message(self, sender: str, recipient: str, content: str, groupe_id: Optional[int] = None):
        cur = self.db.cursor()
        cur.execute("""
            INSERT INTO messages (sender, recipient, groupe_id, content)
            VALUES (?, ?, ?, ?)
        """, (sender, recipient, groupe_id, content))
        self.db.commit()
        return cur.lastrowid

    def obtenir_messages(self, groupe_id: Optional[int] = None, limit: int = 200) -> List[Dict[str, Any]]:
        cur = self.db.cursor()
        if groupe_id:
            cur.execute("SELECT * FROM messages WHERE groupe_id = ? ORDER BY sent_at DESC LIMIT ?", 
                       (groupe_id, limit))
        else:
            cur.execute("SELECT * FROM messages ORDER BY sent_at DESC LIMIT ?", (limit,))
        return [dict(r) for r in cur.fetchall()]


def creer_gestionnaire_db() -> Tuple[DBManager, MembresManager, EvenementsManager, GroupesManager, PresencesManager, MessagesManager]:
    db = DBManager()
    membres_mgr = MembresManager(db)
    evenements_mgr = EvenementsManager(db)
    groupes_mgr = GroupesManager(db)
    presences_mgr = PresencesManager(db)
    messages_mgr = MessagesManager(db)
    
    # Garder une référence pour clear_caches
    db._managers = [membres_mgr, evenements_mgr, groupes_mgr, presences_mgr, messages_mgr]
    
    return db, membres_mgr, evenements_mgr, groupes_mgr, presences_mgr, messages_mgr