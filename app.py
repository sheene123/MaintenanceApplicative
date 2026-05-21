# fichier : app.py
from datetime import datetime
import sqlite3
import streamlit as st

# ==========================================================
# 1. LOGIQUE MÉTIER & PERSISTANCE (SQLITE)
#    → Séparation logique métier / interface = maintenance perfective
#    → Passage session_state → SQLite = maintenance adaptative
#    → Ajout de nouvelles colonnes = maintenance évolutive + adaptative
# ==========================================================

def init_db():
    """
    Crée la table ou y ajoute les nouvelles colonnes si nécessaire (migration).

    - Maintenance adaptative : adaptation du stockage pour assurer la persistance.
    - Maintenance évolutive : ajout de nouvelles colonnes (priority, due_date).
    - Maintenance corrective : gestion propre des erreurs SQLite lors des migrations.
    """
    conn = sqlite3.connect("todo.db")
    cursor = conn.cursor()

    # Création initiale de la table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            done BOOLEAN NOT NULL DEFAULT 0
        )
    """
    )

    # MIGRATION : ajout de colonnes si elles n'existent pas
    try:
        cursor.execute(
            "ALTER TABLE tasks ADD COLUMN priority TEXT NOT NULL DEFAULT 'Moyenne'"
        )
        cursor.execute("ALTER TABLE tasks ADD COLUMN due_date TEXT")
    except sqlite3.OperationalError:
        # Maintenance corrective : éviter crash si colonne existe déjà
        pass

    conn.commit()
    conn.close()


def get_all_tasks():
    """
    Récupère toutes les tâches triées par priorité et date.

    - Maintenance perfective : tri SQL avancé pour améliorer l’UX.
    - Maintenance évolutive : ajout de nouvelles métadonnées (priority, due_date).
    """
    conn = sqlite3.connect("todo.db")
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, title, done, priority, due_date FROM tasks
        ORDER BY 
            done ASC,
            CASE priority 
                WHEN 'Haute' THEN 1 
                WHEN 'Moyenne' THEN 2 
                WHEN 'Basse' THEN 3 
            END ASC,
            due_date ASC
    """
    )
    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "id": r[0],
            "title": r[1],
            "done": bool(r[2]),
            "priority": r[3],
            "due_date": r[4],
        }
        for r in rows
    ]


def add_task(title, priority, due_date):
    """
    Ajoute une tâche avec priorité et date.

    - Maintenance évolutive : ajout de nouvelles fonctionnalités (priorité + date).
    - Maintenance corrective : blocage des doublons et titres vides.
    - Maintenance perfective : nettoyage du titre pour éviter erreurs utilisateur.
    """
    clean_title = title.strip()
    if not clean_title:
        return False

    conn = sqlite3.connect("todo.db")
    cursor = conn.cursor()

    # Vérification des doublons → amélioration UX
    cursor.execute(
        "SELECT COUNT(*) FROM tasks WHERE LOWER(title) = LOWER(?)", (clean_title,)
    )
    existe = cursor.fetchone()[0] > 0

    if existe:
        conn.close()
        return False

    date_str = due_date.strftime("%Y-%m-%d") if due_date else None

    cursor.execute(
        "INSERT INTO tasks (title, done, priority, due_date) VALUES (?, 0, ?, ?)",
        (clean_title, priority, date_str),
    )
    conn.commit()
    conn.close()
    return True


def update_task(task_id, new_title, new_priority, new_due_date):
    """
    Modifie une tâche existante.

    - Maintenance évolutive : ajout de la modification complète.
    - Maintenance corrective : empêche doublons et titres vides.
    - Maintenance perfective : amélioration de la qualité des données.
    """
    clean_title = new_title.strip()
    if not clean_title:
        return False

    conn = sqlite3.connect("todo.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT COUNT(*) FROM tasks WHERE LOWER(title) = LOWER(?) AND id != ?",
        (clean_title, task_id),
    )
    existe = cursor.fetchone()[0] > 0

    if existe:
        conn.close()
        return False

    date_str = new_due_date.strftime("%Y-%m-%d") if new_due_date else None

    cursor.execute(
        "UPDATE tasks SET title = ?, priority = ?, due_date = ? WHERE id = ?",
        (clean_title, new_priority, date_str, task_id),
    )
    conn.commit()
    conn.close()
    return True


def mark_as_done(task_id):
    """
    Marque une tâche comme terminée.

    - Maintenance évolutive : ajout d’une action utilisateur.
    """
    conn = sqlite3.connect("todo.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE tasks SET done = 1 WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()


def delete_task(task_id):
    """
    Supprime une tâche.

    - Maintenance évolutive : ajout de la suppression.
    - Maintenance corrective : évite accumulation de données inutiles.
    """
    conn = sqlite3.connect("todo.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()


# ==========================================================
# 2. INTERFACE UTILISATEUR (STREAMLIT)
#    → Séparation UI / logique métier = maintenance perfective
#    → Ajout de filtres, priorités, dates = maintenance évolutive
#    → Messages d’erreur = maintenance perfective (UX)
# ==========================================================

init_db()

st.title("📝 Ma TodoList Professionnelle")

# Gestion des messages → amélioration UX
if "msg_error" not in st.session_state:
    st.session_state["msg_error"] = None
if "msg_success" not in st.session_state:
    st.session_state["msg_success"] = None

# ----------------------------------------------------------
# FORMULAIRE D'AJOUT
# → Maintenance évolutive : ajout priorité + date
# → Maintenance perfective : meilleure UX (colonnes, messages)
# ----------------------------------------------------------
with st.form(key="add_task_form", clear_on_submit=True):
    new_task = st.text_input("Ajouter une tâche")

    f_col1, f_col2 = st.columns(2)
    with f_col1:
        priority = st.selectbox("Priorité", ["Basse", "Moyenne", "Haute"], index=1)
    with f_col2:
        due_date = st.date_input("Date d'échéance", value=datetime.today())

    submit_button = st.form_submit_button(label="Ajouter la tâche")

if submit_button:
    if new_task.strip() == "":
        # Maintenance corrective : empêcher saisie invalide
        st.session_state["msg_error"] = "⚠️ Le titre de la tâche ne peut pas être vide."
        st.session_state["msg_success"] = None
        st.rerun()
    else:
        creation_reussie = add_task(new_task, priority, due_date)
        if creation_reussie:
            st.session_state["msg_success"] = f"✅ Tâche '{new_task.strip()}' ajoutée !"
            st.session_state["msg_error"] = None
            st.rerun()
        else:
            st.session_state["msg_error"] = (
                f"🚨 Doublon détecté ! La tâche '**{new_task.strip()}**' existe déjà."
            )
            st.session_state["msg_success"] = None
            st.rerun()

# Affichage des messages → maintenance perfective
if st.session_state["msg_error"]:
    st.error(st.session_state["msg_error"])
    st.session_state["msg_error"] = None

if st.session_state["msg_success"]:
    st.success(st.session_state["msg_success"])
    st.session_state["msg_success"] = None


# ----------------------------------------------------------
# LISTE DES TÂCHES + ONGLET FILTRE
# → Maintenance évolutive : ajout des onglets (toutes / à faire / terminées)
# → Maintenance perfective : meilleure lisibilité
# ----------------------------------------------------------

def get_priority_badge(level):
    """
    Retourne un badge visuel selon la priorité.

    - Maintenance perfective : amélioration UX (couleurs, icônes).
    """
    if level == "Haute":
        return "🔴 Haute"
    elif level == "Moyenne":
        return "🟡 Moyenne"
    return "🔵 Basse"


st.subheader("Liste des tâches")
tasks = get_all_tasks()

tasks_todo = [t for t in tasks if not t["done"]]
tasks_done = [t for t in tasks if t["done"]]

# Onglets → maintenance évolutive
tab_all, tab_todo, tab_done = st.tabs(
    [
        f"📋 Toutes ({len(tasks)})",
        f"⏳ À faire ({len(tasks_todo)})",
        f"✅ Terminées ({len(tasks_done)})",
    ]
)


def afficher_liste_taches(liste_a_afficher, prefix):
    """
    Affiche une liste de tâches avec actions.

    - Maintenance évolutive : ajout modification + suppression + priorité + date.
    - Maintenance perfective : affichage structuré, colonnes, badges.
    """
    if not liste_a_afficher:
        st.info("Aucune tâche dans cette catégorie.")
        return

    for t in liste_a_afficher:
        col1, col2, col3, col4, col5 = st.columns([0.4, 0.2, 0.1, 0.1, 0.2])

        # Formatage date SQL → UX améliorée
        date_formatee = "Pas de date"
        if t["due_date"]:
            dt = datetime.strptime(t["due_date"], "%Y-%m-%d")
            date_formatee = dt.strftime("%d/%m/%Y")

        with col1:
            if t["done"]:
                st.write(f"✅ ~~{t['title']}~~")
            else:
                st.write(f"⏳ **{t['title']}**")

        with col2:
            badge = get_priority_badge(t["priority"])
            st.caption(f"{badge}  \n📅 {date_formatee}")

        with col3:
            if not t["done"]:
                if st.button("Fait", key=f"done_{prefix}_{t['id']}"):
                    mark_as_done(t["id"])
                    st.rerun()

        with col4:
            if not t["done"]:
                with st.popover("✏️", help="Modifier la tâche"):
                    st.write(f"Modifier : *{t['title']}*")
                    with st.form(
                        key=f"edit_form_{prefix}_{t['id']}",
                        clear_on_submit=False,
                    ):
                        edited_title = st.text_input(
                            "Nouveau titre",
                            value=t["title"],
                            key=f"input_t_{prefix}_{t['id']}",
                        )
                        edited_priority = st.selectbox(
                            "Priorité",
                            ["Basse", "Moyenne", "Haute"],
                            index=["Basse", "Moyenne", "Haute"].index(
                                t["priority"]
                            ),
                            key=f"input_p_{prefix}_{t['id']}",
                        )

                        current_date_obj = (
                            datetime.strptime(t["due_date"], "%Y-%m-%d").date()
                            if t["due_date"]
                            else datetime.today().date()
                        )
                        edited_date = st.date_input(
                            "Échéance",
                            value=current_date_obj,
                            key=f"input_d_{prefix}_{t['id']}",
                        )

                        save_edit = st.form_submit_button("Enregistrer")

                    if save_edit:
                        modif_reussie = update_task(
                            t["id"], edited_title, edited_priority, edited_date
                        )
                        if modif_reussie:
                            st.session_state["msg_success"] = "Tâche mise à jour !"
                            st.rerun()
                        else:
                            st.session_state["msg_error"] = (
                                f"🚨 Doublon ou titre vide pour '{edited_title.strip()}'"
                            )
                            st.rerun()

        with col5:
            if st.button("Supprimer", key=f"del_{prefix}_{t['id']}"):
                delete_task(t["id"])
                st.rerun()


with tab_all:
    afficher_liste_taches(tasks, prefix="all")

with tab_todo:
    afficher_liste_taches(tasks_todo, prefix="todo")

with tab_done:
    afficher_liste_taches(tasks_done, prefix="done")
