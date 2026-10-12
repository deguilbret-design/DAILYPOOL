import json
import os
import pandas as pd
import streamlit as st

DATA_FILE = "pool_data.json"

# Règles de calcul des points
POINTS_BUT = 2
POINTS_PASSE = 1
POINTS_VICTOIRE = 2
POINTS_BLANCHISSAGE = 3

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        return {
            "participants": [],
            "joueurs": []  # Structure unique par joueur
        }

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

st.set_page_config(page_title="Pool de Hockey - Journalier", page_icon="🏒", layout="wide")

data = load_data()

st.title("🏒 Pool de Hockey - Suivi Journalier")
st.markdown("Gère tes matchs du soir, consulte le classement et fais un **RESET** quotidien pour repartir à zéro le lendemain.")

# --- BARRE LATÉRALE ---
st.sidebar.header("⚙️ Configuration & Actions")
menu = st.sidebar.radio("Navigation", ["Tableau de bord & Stats", "Gestion des Joueurs / Participants"])

st.sidebar.markdown("---")

# Bouton RESET Journalier
if st.sidebar.button("🔄 RESET Journalier (Mettre stats à 0)", type="primary"):
    for j in data["joueurs"]:
        j["buts"] = 0
        j["passes"] = 0
        j["victoires"] = 0
        j["blanchissages"] = 0
    save_data(data)
    st.sidebar.success("Toutes les statistiques du jour ont été remises à zéro !")
    st.rerun()

# --- SECTION 1 : GESTION ---
if menu == "Gestion des Joueurs / Participants":
    st.header("👥 Gestion des Participants et des Joueurs")
    
    with st.form("add_participant_form"):
        st.subheader("1. Ajouter un participant")
        nouveau_participant = st.text_input("Nom du participant")
        submit_p = st.form_submit_button("Ajouter le participant")
        if submit_p:
            if nouveau_participant and nouveau_participant not in data["participants"]:
                data["participants"].append(nouveau_participant)
                save_data(data)
                st.success(f"Participant '{nouveau_participant}' ajouté avec succès !")
                st.rerun()
            elif not nouveau_participant:
                st.error("Le nom ne peut pas être vide.")
            else:
                st.warning("Ce participant existe déjà.")

    st.markdown("---")

    with st.form("add_player_form"):
        st.subheader("2. Ajouter un joueur unique et l'associer aux participants")
        if data["participants"]:
            nom_joueur = st.text_input("Nom du joueur (ex: Cale Makar)")
            position = st.selectbox("Position", ["Attaquant", "Défenseur", "Gardien"])
            
            st.markdown("**Coche les participants qui ont choisi ce joueur :**")
            participant_checks = {}
            for p in data["participants"]:
                participant_checks[p] = st.checkbox(p, key=f"chk_{p}")

            submit_j = st.form_submit_button("Enregistrer ce joueur")
            
            if submit_j:
                if nom_joueur:
                    participants_selectionnes = [p for p, selected in participant_checks.items() if selected]
                    
                    joueur_existant = next((j for j in data["joueurs"] if j["nom"].lower() == nom_joueur.lower()), None)
                    
                    if joueur_existant:
                        # Ajouter les nouveaux participants s'ils n'y sont pas déjà
                        for p in participants_selectionnes:
                            if p not in joueur_existant["participants"]:
                                joueur_existant["participants"].append(p)
                        save_data(data)
                        st.success(f"Joueur {nom_joueur} mis à jour avec les nouveaux participants !")
                        st.rerun()
                    else:
                        data["joueurs"].append({
                            "nom": nom_joueur,
                            "position": position,
                            "participants": participants_selectionnes,
                            "buts": 0,
                            "passes": 0,
                            "victoires": 0,
                            "blanchissages": 0
                        })
                        save_data(data)
                        st.success(f"Joueur {nom_joueur} ajouté avec succès !")
                        st.rerun()
                else:
                    st.error("Le nom du joueur est requis.")
        else:
            st.info("Veuillez d'abord ajouter au moins un participant.")

    # Affichage de la liste actuelle
    st.subheader("📋 Liste des joueurs uniques enregistrés")
    if data["joueurs"]:
        df_show = pd.DataFrame([
            {
                "Joueur": j["nom"],
                "Position": j["position"],
                "Participants l'ayant choisi": ", ".join(j["participants"])
            } for j in data["joueurs"]
        ])
        st.dataframe(df_show, use_container_width=True)
        
        joueur_a_supprimer = st.selectbox("Sélectionner un joueur à supprimer de la liste", [j["nom"] for j in data["joueurs"]])
        if st.button("Supprimer ce joueur"):
            data["joueurs"] = [j for j in data["joueurs"] if j["nom"] != joueur_a_supprimer]
            save_data(data)
            st.success("Joueur supprimé.")
            st.rerun()
    else:
        st.info("Aucun joueur enregistré pour le moment.")

# --- SECTION 2 : TABLEAU DE BORD & STATS ---
elif menu == "Tableau de bord & Stats":
    
    if not data["joueurs"]:
        st.info("👋 Bienvenue ! Commence par aller dans l'onglet **Gestion des Joueurs / Participants** pour configurer ton pool.")
    else:
        st.header("⚡ Saisie des statistiques de la soirée")
        st.markdown("Chaque joueur n'apparaît qu'**une seule fois**. Modifie ses stats et clique sur enregistrer.")

        df_saisie = pd.DataFrame(data["joueurs"])
        colonnes_edition = ["nom", "position", "buts", "passes", "victoires", "blanchissages"]
        
        edited_df = st.data_editor(
            df_saisie[colonnes_edition],
            num_rows="fixed",
            use_container_width=True,
            key="grid_stats"
        )

        if st.button("💾 Enregistrer les modifications des stats", type="primary"):
            for index, row in edited_df.iterrows():
                data["joueurs"][index]["buts"] = int(row["buts"])
                data["joueurs"][index]["passes"] = int(row["passes"])
                data["joueurs"][index]["victoires"] = int(row["victoires"])
                data["joueurs"][index]["blanchissages"] = int(row["blanchissages"])
            save_data(data)
            st.success("Statistiques enregistrées avec succès !")
            st.rerun()

        st.markdown("---")

        # --- CLASSEMENT DES PARTICIPANTS ---
        st.header("🏆 Classement Général des Participants")

        classement_data = []
        for p in data["participants"]:
            # Récupérer tous les joueurs qui ont ce participant dans leur liste
            joueurs_p = [j for j in data["joueurs"] if p in j.get("participants", [])]
            
            total_buts = sum(j.get("buts", 0) for j in joueurs_p)
            total_passes = sum(j.get("passes", 0) for j in joueurs_p)
            total_victoires = sum(j.get("victoires", 0) for j in joueurs_p)
            total_blanchissages = sum(j.get("blanchissages", 0) for j in joueurs_p)
            
            total_pts = 0
            for j in joueurs_p:
                if j["position"] == "Gardien":
                    total_pts += (j.get("victoires", 0) * POINTS_VICTOIRE) + (j.get("blanchissages", 0) * POINTS_BLANCHISSAGE) + (j.get("buts", 0) * POINTS_BUT) + (j.get("passes", 0) * POINTS_PASSE)
                else:
                    total_pts += (j.get("buts", 0) * POINTS_BUT) + (j.get("passes", 0) * POINTS_PASSE)

            classement_data.append({
                "Participant": p,
                "Buts": total_buts,
                "Passes": total_passes,
                "Victoires (Gardiens)": total_victoires,
                "Blanchissages": total_blanchissages,
                "Points Totaux": total_pts
            })

        df_classement = pd.DataFrame(classement_data)

        if not df_classement.empty:
            col_tri, ascending_order = st.columns(2)
            with col_tri:
                critere_tri = st.selectbox("Trier le classement par :", ["Points Totaux", "Buts", "Passes", "Victoires (Gardiens)", "Blanchissages", "Participant"], index=0)
            with ascending_order:
                ordre = st.radio("Ordre de tri", ["Décroissant (Haut en bas)", "Croissant"], index=0)
                is_ascending = True if ordre == "Croissant" else False

            df_classement = df_classement.sort_values(by=critere_tri, ascending=is_ascending).reset_index(drop=True)
            df_classement.index = df_classement.index + 1

            st.dataframe(df_classement, use_container_width=True)
        else:
            st.info("Aucun participant dans le classement pour l'instant.")
