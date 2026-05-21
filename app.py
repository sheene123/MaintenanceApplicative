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
    # On transforme en dictionnaire pour garder le code propre
    return [{"id": r[0], "title": r[1], "done": bool(r[2])} for r in rows]


def add_task(title):
    """Ajoute une nouvelle tâche."""
    if title.strip():
        conn = sqlite3.connect("todo.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO tasks (title, done) VALUES (?, 0)", (title,))
        conn.commit()
        conn.close()


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

# Initialisation de la base au démarrage
init_db()

st.title("📝 Ma TodoList Sécurisée")

# Formulaire d'ajout
with st.form(key="add_task_form", clear_on_submit=True):
    new_task = st.text_input("Ajouter une tâche")
    submit_button = st.form_submit_button(label="Ajouter")

if submit_button:
    add_task(new_task)
    st.rerun()  # Recharge la page pour afficher la nouvelle tâche

# Affichage des tâches
st.subheader("Liste des tâches")
tasks = get_all_tasks()

if not tasks:
    st.info("Aucune tâche pour le moment. C'est l'heure de se reposer !")

for t in tasks:
    # On crée 3 colonnes : le texte, le bouton fait, le bouton supprimer
    col1, col2, col3 = st.columns([0.6, 0.2, 0.2])

    with col1:
        if t["done"]:
            st.write(f"✅ ~~{t['title']}~~")
        else:
            st.write(f"⏳ **{t['title']}**")

    with col2:
        # On affiche le bouton uniquement si la tâche n'est pas faite
        if not t["done"]:
            if st.button("Fait", key=f"done_{t['id']}"):
                mark_as_done(t["id"])
                st.rerun()

    with col3:
        if st.button("Supprimer", key=f"del_{t['id']}"):
            delete_task(t["id"])
            st.rerun()