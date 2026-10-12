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
            data = json.load(f)
            for j in data.get("joueurs", []):
                if "participants" not in j:
                    j["participants"] = []
            return data
    else:
        return {
            "participants": [],
            "joueurs": []
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
menu = st.sidebar.radio("Navigation", [
    "Tableau de bord & Stats", 
    "Gestion des Joueurs / Participants", 
    "Alignements par Participant"
])

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
    
    # 1. Gestion des Participants
    col1, col2 = st.columns(2)
    with col1:
        with st.form("add_participant_form"):
            st.subheader("Ajouter un participant")
            nouveau_participant = st.text_input("Nom du participant")
            submit_p = st.form_submit_button("Ajouter")
            if submit_p:
                if nouveau_participant and nouveau_participant not in data["participants"]:
                    data["participants"].append(nouveau_participant)
                    save_data(data)
                    st.success(f"'{nouveau_participant}' ajouté !")
                    st.rerun()
                elif not nouveau_participant:
                    st.error("Le nom ne peut pas être vide.")
                else:
                    st.warning("Ce participant existe déjà.")

    with col2:
        if data["participants"]:
            with st.form("del_participant_form"):
                st.subheader("Supprimer un participant")
                part_a_supprimer = st.selectbox("Participant", data["participants"])
                submit_del_p = st.form_submit_button("Supprimer")
                if submit_del_p:
                    data["participants"].remove(part_a_supprimer)
                    for j in data["joueurs"]:
                        if part_a_supprimer in j["participants"]:
                            j["participants"].remove(part_a_supprimer)
                    save_data(data)
                    st.success(f"'{part_a_supprimer}' supprimé !")
                    st.rerun()

    st.markdown("---")

    # 2. Ajouter un nouveau joueur
    with st.expander("➕ Ajouter un nouveau joueur unique"):
        with st.form("add_player_form"):
            nom_joueur = st.text_input("Nom du joueur (ex: Cale Makar)")
            position = st.selectbox("Position", ["Attaquant", "Défenseur", "Gardien"])
            
            st.markdown("**Coche les participants qui ont choisi ce joueur :**")
            participant_checks = {}
            for p in data["participants"]:
                participant_checks[p] = st.checkbox(p, key=f"chk_new_{p}")

            submit_j = st.form_submit_button("Enregistrer le joueur")
            
            if submit_j:
                if nom_joueur:
                    participants_selectionnes = [p for p, selected in participant_checks.items() if selected]
                    joueur_existant = next((j for j in data["joueurs"] if j["nom"].lower() == nom_joueur.lower()), None)
                    
                    if joueur_existant:
                        st.error("Ce joueur existe déjà. Utilise la section de modification ci-dessous pour ajuster ses participants.")
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

    st.markdown("---")

    # 3. Modifier rapidement les participants d'un joueur existant (Pré-coché par défaut)
    st.subheader("✏️ Modifier les participants d'un joueur existant")
    if data["joueurs"] and data["participants"]:
        joueurs_tries = sorted(data["joueurs"], key=lambda x: x["nom"].lower())
        noms_joueurs = [j["nom"] for j in joueurs_tries]
        
        selected_player_name = st.selectbox("Sélectionne un joueur dans la liste (A-Z)", noms_joueurs)
        
        joueur_obj = next(j for j in data["joueurs"] if j["nom"] == selected_player_name)
        
        with st.form("edit_player_form"):
            st.markdown(f"**Modification pour : {joueur_obj['nom']} ({joueur_obj['position']})**")
            st.markdown("Les participants qui ont déjà choisi ce joueur sont **déjà cochés**. Ajoute ou retire des sélections selon tes besoins :")
            
            edit_checks = {}
            for p in data["participants"]:
                deja_present = p in joueur_obj.get("participants", [])
                edit_checks[p] = st.checkbox(p, value=deja_present, key=f"edit_chk_{p}")
                
            submit_edit = st.form_submit_button("Mettre à jour les participants")
            
            if submit_edit:
                nouveaux_participants = [p for p, selected in edit_checks.items() if selected]
                joueur_obj["participants"] = nouveaux_participants
                save_data(data)
                st.success(f"Les participants pour {joueur_obj['nom']} ont été mis à jour avec succès !")
                st.rerun()

        st.markdown("---")
        
        with st.expander("🗑️ Supprimer un joueur de la liste"):
            joueur_a_supprimer = st.selectbox("Choisir le joueur à supprimer", noms_joueurs, key="del_p_list")
            if st.button("Supprimer ce joueur définitivement"):
                data["joueurs"] = [j for j in data["joueurs"] if j["nom"] != joueur_a_supprimer]
                save_data(data)
                st.success("Joueur supprimé.")
                st.rerun()

    # Affichage de la liste actuelle globale
    st.subheader("📋 Liste globale des joueurs enregistrés")
    if data["joueurs"]:
        df_show = pd.DataFrame([
            {
                "Joueur": j["nom"],
                "Position": j["position"],
                "Participants l'ayant choisi": ", ".join(j.get("participants", []))
            } for j in sorted(data["joueurs"], key=lambda x: x["nom"].lower())
        ])
        df_show.index = df_show.index + 1
        st.dataframe(df_show, use_container_width=True)
    else:
        st.info("Aucun joueur enregistré pour le moment.")

# --- SECTION 2 : TABLEAU DE BORD & STATS ---
elif menu == "Tableau de bord & Stats":
    
    if not data["joueurs"]:
        st.info("👋 Bienvenue ! Commence par aller dans l'onglet **Gestion des Joueurs / Participants** pour configurer ton pool.")
    else:
        st.header("⚡ Saisie des statistiques de la soirée")
        st.markdown("Les joueurs sont triés **par ordre alphabétique** pour faciliter la saisie.")

        joueurs_tries_stats = sorted(data["joueurs"], key=lambda x: x["nom"].lower())
        
        df_saisie = pd.DataFrame(joueurs_tries_stats)
        colonnes_edition = ["nom", "position", "buts", "passes", "victoires", "blanchissages"]
        
        edited_df = st.data_editor(
            df_saisie[colonnes_edition],
            num_rows="fixed",
            use_container_width=True,
            key="grid_stats"
        )

        if st.button("💾 Enregistrer les modifications des stats", type="primary"):
            for index, row in edited_df.iterrows():
                nom_j = row["nom"]
                for j in data["joueurs"]:
                    if j["nom"] == nom_j:
                        j["buts"] = int(row["buts"])
                        j["passes"] = int(row["passes"])
                        j["victoires"] = int(row["victoires"])
                        j["blanchissages"] = int(row["blanchissages"])
            save_data(data)
            st.success("Statistiques enregistrées avec succès !")
            st.rerun()

        st.markdown("---")

        # --- CLASSEMENT DES PARTICIPANTS ---
        st.header("🏆 Classement Général des Participants")

        classement_data = []
        for p in data["participants"]:
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

# --- SECTION 3 : ALIGNEMENTS PAR PARTICIPANT ---
elif menu == "Alignements par Participant":
    st.header("📋 Vérification des alignements par participant")
    
    if not data["participants"]:
        st.info("Aucun participant enregistré.")
    else:
        participant_selectionne = st.selectbox("Sélectionne un participant pour voir son équipe", sorted(data["participants"]))
        
        # Filtrer les joueurs de ce participant
        joueurs_du_participant = [
            j for j in data["joueurs"] if participant_selectionne in j.get("participants", [])
        ]
        
        # Tri personnalisé : Attaquants d'abord, puis Défenseurs, puis Gardiens (et ordre alphabétique du nom à l'intérieur)
        ordre_positions = {"Attaquant": 1, "Défenseur": 2, "Gardien": 3}
        
        joueurs_du_participant = sorted(
            joueurs_du_participant, 
            key=lambda x: (ordre_positions.get(x["position"], 4), x["nom"].lower())
        )
        
        if joueurs_du_participant:
            st.markdown(f"**Équipe de {participant_selectionne}** ({len(joueurs_du_participant)} joueur(s) enregistré(s)) :")
            
            df_part_show = pd.DataFrame([
                {
                    "Position": j["position"],
                    "Joueur": j["nom"],
                    "Buts": j.get("buts", 0),
                    "Passes": j.get("passes", 0),
                    "Victoires": j.get("victoires", 0),
                    "Blanchissages": j.get("blanchissages", 0)
                } for j in joueurs_du_participant
            ])
            # Numérotation de 1 à 15 (ou plus)
            df_part_show.index = df_part_show.index + 1
            st.dataframe(df_part_show, use_container_width=True)
        else:
            st.info(f"Aucun joueur n'a encore été associé à {participant_selectionne}.")
