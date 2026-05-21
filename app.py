# fichier : app.py
import sqlite3
import streamlit as st

# ==========================================
# 1. LOGIQUE MÉTIER & PERSISTANCE (SQLITE)
# ==========================================


def init_db():
    """Crée la table des tâches si elle n'existe pas encore."""
    conn = sqlite3.connect("todo.db")
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            done BOOLEAN NOT NULL DEFAULT 0
        )
    """
    )
    conn.commit()
    conn.close()


def get_all_tasks():
    """Récupère toutes les tâches de la base de données."""
    conn = sqlite3.connect("todo.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, done FROM tasks")
    rows = cursor.fetchall()
    conn.close()
    return [{"id": r[0], "title": r[1], "done": bool(r[2])} for r in rows]


def add_task(title):
    """Ajoute une nouvelle tâche après vérification des doublons."""
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

    cursor.execute(
        "INSERT INTO tasks (title, done) VALUES (?, 0)", (clean_title,)
    )
    conn.commit()
    conn.close()
    return True


def update_task(task_id, new_title):
    """Modifie le titre d'une tâche existante après vérification des doublons."""
    clean_title = new_title.strip()
    if not clean_title:
        return False

    conn = sqlite3.connect("todo.db")
    cursor = conn.cursor()

    # On vérifie que le nouveau nom n'existe pas déjà sur une AUTRE tâche (id différent)
    cursor.execute(
        "SELECT COUNT(*) FROM tasks WHERE LOWER(title) = LOWER(?) AND id != ?",
        (clean_title, task_id),
    )
    existe = cursor.fetchone()[0] > 0

    if existe:
        conn.close()
        return False

    cursor.execute(
        "UPDATE tasks SET title = ? WHERE id = ?", (clean_title, task_id)
    )
    conn.commit()
    conn.close()
    return True


def mark_as_done(task_id):
    """Marque une tâche comme terminée."""
    conn = sqlite3.connect("todo.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE tasks SET done = 1 WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()


def delete_task(task_id):
    """Supprime définitivement une tâche."""
    conn = sqlite3.connect("todo.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()


# ==========================================
# 2. INTERFACE UTILISATEUR (STREAMLIT)
# ==========================================

init_db()

st.title("📝 Ma TodoList Sécurisée")

# Initialisation des variables de message
if "msg_error" not in st.session_state:
    st.session_state["msg_error"] = None
if "msg_success" not in st.session_state:
    st.session_state["msg_success"] = None

# Formulaire d'ajout
with st.form(key="add_task_form", clear_on_submit=True):
    new_task = st.text_input("Ajouter une tâche")
    submit_button = st.form_submit_button(label="Ajouter")

if submit_button:
    if new_task.strip() == "":
        st.session_state["msg_error"] = (
            "⚠️ Le titre de la tâche ne peut pas être vide."
        )
        st.session_state["msg_success"] = None
        st.rerun()
    else:
        creation_reussie = add_task(new_task)
        if creation_reussie:
            st.session_state["msg_success"] = (
                f"✅ Tâche '{new_task.strip()}' ajoutée avec succès !"
            )
            st.session_state["msg_error"] = None
            st.rerun()
        else:
            st.session_state["msg_error"] = (
                f"🚨 Doublon détecté ! La tâche '**{new_task.strip()}**' existe déjà."
            )
            st.session_state["msg_success"] = None
            st.rerun()

# Affichage des alertes
if st.session_state["msg_error"]:
    st.error(st.session_state["msg_error"])
    st.session_state["msg_error"] = None

if st.session_state["msg_success"]:
    st.success(st.session_state["msg_success"])
    st.session_state["msg_success"] = None


# Affichage des tâches
st.subheader("Liste des tâches")
tasks = get_all_tasks()

if not tasks:
    st.info("Aucune tâche pour le moment. C'est l'heure de se reposer !")

for t in tasks:
    # J'ai ajusté la taille des colonnes pour faire de la place au bouton modifier [col3]
    col1, col2, col3, col4 = st.columns([0.5, 0.15, 0.15, 0.2])

    with col1:
        if t["done"]:
            st.write(f"✅ ~~{t['title']}~~")
        else:
            st.write(f"⏳ **{t['title']}**")

    with col2:
        if not t["done"]:
            if st.button("Fait", key=f"done_{t['id']}"):
                mark_as_done(t["id"])
                st.rerun()

    # COLONNE DE MODIFICATION
    with col3:
        if not t["done"]:
            # On crée une fenêtre flottante (popover) attachée à un bouton icône crayon
            with st.popover("✏️", help="Modifier la tâche"):
                st.write(f"Modifier : *{t['title']}*")
                # Un sous-formulaire pour valider le changement
                with st.form(key=f"edit_form_{t['id']}", clear_on_submit=False):
                    edited_title = st.text_input(
                        "Nouveau titre", value=t["title"]
                    )
                    save_edit = st.form_submit_button("Enregistrer")

                if save_edit:
                    modif_reussie = update_task(t["id"], edited_title)
                    if modif_reussie:
                        st.session_state["msg_success"] = "Tâche modifiée !"
                        st.rerun()
                    else:
                        st.session_state["msg_error"] = (
                            f"🚨 Modification impossible : '{edited_title.strip()}' est vide ou existe déjà."
                        )
                        st.rerun()

    with col4:
        if st.button("Supprimer", key=f"del_{t['id']}"):
            delete_task(t["id"])
            st.rerun()