# fichier : app.py
from datetime import datetime
import sqlite3
import streamlit as st

# ==========================================
# 1. LOGIQUE MÉTIER & PERSISTANCE (SQLITE)
# ==========================================


def init_db():
    """Crée la table ou y ajoute les nouvelles colonnes si nécessaire (migration)."""
    conn = sqlite3.connect("todo.db")
    cursor = conn.cursor()

    # Création initiale de la table de base
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            done BOOLEAN NOT NULL DEFAULT 0
        )
    """
    )

    # MIGRATION SÉCURISÉE : On ajoute les nouvelles colonnes si elles n'existent pas encore
    try:
        cursor.execute(
            "ALTER TABLE tasks ADD COLUMN priority TEXT NOT NULL DEFAULT 'Moyenne'"
        )
        cursor.execute("ALTER TABLE tasks ADD COLUMN due_date TEXT")
    except sqlite3.OperationalError:
        # Si les colonnes existent déjà, SQLite lève une erreur, on l'ignore proprement
        pass

    conn.commit()
    conn.close()


def get_all_tasks():
    """Récupère toutes les tâches triées par date d'échéance (les plus proches d'abord)

    puis par niveau de priorité.
    """
    conn = sqlite3.connect("todo.db")
    cursor = conn.cursor()

    # Tri SQL complexe : les tâches urgentes et proches sortent en premier
    # CASE WHEN attribue un poids pour trier correctement Haute > Moyenne > Basse
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
    """Ajoute une tâche avec sa priorité et sa date d'échéance."""
    clean_title = title.strip()
    if not clean_title:
        return False

    conn = sqlite3.connect("todo.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT COUNT(*) FROM tasks WHERE LOWER(title) = LOWER(?)", (clean_title,)
    )
    existe = cursor.fetchone()[0] > 0

    if existe:
        conn.close()
        return False

    # Stockage de la date au format texte ISO (AAAA-MM-JJ) pour SQLite
    date_str = due_date.strftime("%Y-%m-%d") if due_date else None

    cursor.execute(
        "INSERT INTO tasks (title, done, priority, due_date) VALUES (?, 0, ?, ?)",
        (clean_title, priority, date_str),
    )
    conn.commit()
    conn.close()
    return True


def update_task(task_id, new_title, new_priority, new_due_date):
    """Modifie l'ensemble des données d'une tâche."""
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
    conn = sqlite3.connect("todo.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE tasks SET done = 1 WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()


def delete_task(task_id):
    conn = sqlite3.connect("todo.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()


# ==========================================
# 2. INTERFACE UTILISATEUR (STREAMLIT)
# ==========================================

init_db()

st.title("📝 Ma TodoList Professionnelle")

if "msg_error" not in st.session_state:
    st.session_state["msg_error"] = None
if "msg_success" not in st.session_state:
    st.session_state["msg_success"] = None

# Formulaire d'ajout enrichi
with st.form(key="add_task_form", clear_on_submit=True):
    new_task = st.text_input("Ajouter une tâche")

    # Utilisation de colonnes pour intégrer proprement les métadonnées
    f_col1, f_col2 = st.columns(2)
    with f_col1:
        priority = st.selectbox(
            "Priorité", ["Basse", "Moyenne", "Haute"], index=1
        )
    with f_col2:
        due_date = st.date_input("Date d'échéance", value=datetime.today())

    submit_button = st.form_submit_button(label="Ajouter la tâche")

if submit_button:
    if new_task.strip() == "":
        st.session_state["msg_error"] = (
            "⚠️ Le titre de la tâche ne peut pas être vide."
        )
        st.session_state["msg_success"] = None
        st.rerun()
    else:
        creation_reussie = add_task(new_task, priority, due_date)
        if creation_reussie:
            st.session_state["msg_success"] = (
                f"✅ Tâche '{new_task.strip()}' ajoutée !"
            )
            st.session_state["msg_error"] = None
            st.rerun()
        else:
            st.session_state["msg_error"] = (
                f"🚨 Doublon détecté ! La tâche '**{new_task.strip()}**' existe déjà."
            )
            st.session_state["msg_success"] = None
            st.rerun()

if st.session_state["msg_error"]:
    st.error(st.session_state["msg_error"])
    st.session_state["msg_error"] = None

if st.session_state["msg_success"]:
    st.success(st.session_state["msg_success"])
    st.session_state["msg_success"] = None


# Configuration des badges de couleur pour les priorités
def get_priority_badge(level):
    if level == "Haute":
        return "🔴 Haute"
    elif level == "Moyenne":
        return "🟡 Moyenne"
    return "🔵 Basse"


# Gestion des filtres d'onglets
st.subheader("Liste des tâches")
tasks = get_all_tasks()

tasks_todo = [t for t in tasks if not t["done"]]
tasks_done = [t for t in tasks if t["done"]]

tab_all, tab_todo, tab_done = st.tabs(
    [
        f"📋 Toutes ({len(tasks)})",
        f"⏳ À faire ({len(tasks_todo)})",
        f"✅ Terminées ({len(tasks_done)})",
    ]
)


def afficher_liste_taches(liste_a_afficher, prefix):
    if not liste_a_afficher:
        st.info("Aucune tâche dans cette catégorie.")
        return

    for t in liste_a_afficher:
        # Ajustement des largeurs de colonne pour intégrer l'affichage des dates et priorités
        col1, col2, col3, col4, col5 = st.columns([0.4, 0.2, 0.1, 0.1, 0.2])

        # Formatage propre de la date récupérée du SQL
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
            # Affichage des métadonnées (Priorité + Date) sous forme de texte stylisé
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

                        # Conversion texte SQL -> objet date pour le sélecteur
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
                                f"🚨 Doublon ou titre vide pour '{edited_title.strip()}'."
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

