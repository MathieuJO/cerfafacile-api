from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
from pypdf import PdfReader, PdfWriter
import os, io
from datetime import datetime

app = Flask(__name__)
CORS(app)

CERFA_PATH = os.path.join(os.path.dirname(__file__), "cerfa.pdf")

@app.route("/")
def index():
    return "CerfaFacile API - OK"

@app.route("/generer-cerfa", methods=["POST"])
def generer_cerfa():
    try:
        d = request.get_json()
        if not d: return jsonify({"error": "Données manquantes"}), 400

        def s(k): return str(d.get(k, "") or "").strip()

        immat         = s("immat").upper()
        marque        = s("marque")
        modele        = s("modele")
        type_variante = s("type_variante")
        genre_nat     = s("genre_national")
        vin           = s("vin")
        mec_j         = s("mec_j").zfill(2)
        mec_m         = s("mec_m").zfill(2)
        mec_a         = s("mec_a")
        km            = s("km")
        num_formule   = s("num_formule")

        vendeur_nom       = s("vendeur_nom").upper()
        vendeur_prenom    = s("vendeur_prenom")
        vendeur_num_voie  = s("vendeur_num_voie")
        vendeur_ext       = s("vendeur_ext")
        vendeur_type_voie = s("vendeur_type_voie")
        vendeur_nom_voie  = s("vendeur_nom_voie")
        vendeur_cp        = s("vendeur_cp")
        vendeur_ville     = s("vendeur_ville")
        vendeur_type      = s("vendeur_type")   # physique / morale
        vendeur_sexe      = s("vendeur_sexe")   # M / F

        acheteur_nom       = s("acheteur_nom").upper()
        acheteur_prenom    = s("acheteur_prenom")
        acheteur_nais_j    = s("acheteur_nais_j").zfill(2)
        acheteur_nais_m    = s("acheteur_nais_m").zfill(2)
        acheteur_nais_a    = s("acheteur_nais_a")
        acheteur_nais_lieu = s("acheteur_nais_lieu")
        acheteur_num_voie  = s("acheteur_num_voie")
        acheteur_ext       = s("acheteur_ext")
        acheteur_type_voie = s("acheteur_type_voie")
        acheteur_nom_voie  = s("acheteur_nom_voie")
        acheteur_cp        = s("acheteur_cp")
        acheteur_ville     = s("acheteur_ville")
        acheteur_type      = s("acheteur_type")
        acheteur_sexe      = s("acheteur_sexe")

        type_cession = s("type_cession")  # ceder / destruction
        vente_j      = s("vente_j").zfill(2)
        vente_m      = s("vente_m").zfill(2)
        vente_a      = s("vente_a")
        vente_h      = s("vente_h").zfill(2)
        vente_min    = s("vente_min").zfill(2)
        lieu_cession = s("lieu_cession")
        date_str     = f"{vente_j}/{vente_m}/{vente_a}"

        # Identité complète vendeur/acheteur
        identite_vendeur  = f"{vendeur_nom} {vendeur_prenom}"
        identite_acheteur = f"{acheteur_nom} {acheteur_prenom}"

        # Radio vendeur type : /1=personne morale /2=personne physique
        radio_vendeur_type  = "/2" if vendeur_type == "physique" else "/1"
        # Radio vendeur sexe : /1=M /2=F
        radio_vendeur_sexe  = "/1" if vendeur_sexe == "M" else "/2"
        radio_acheteur_type = "/2" if acheteur_type == "physique" else "/1"
        radio_acheteur_sexe = "/1" if acheteur_sexe == "M" else "/2"
        # Radio cession : /1=céder /2=destruction
        radio_cession = "/1" if type_cession == "ceder" else "/2"
        # Radio CI présent : /1=OUI /2=NON
        ci = s("ci_present")
        radio_ci = "/1" if ci == "oui" else "/2"

        reader = PdfReader(CERFA_PATH)
        writer = PdfWriter()
        writer.append(reader)

        fields = {}
        for p in [1, 2]:
            px = f"topmostSubform[0].Page{p}[0]"
            fields.update({
                # Véhicule
                f"{px}.num_Immatriculation[0]":              immat,
                f"{px}.num_Identification[0]":               vin,
                f"{px}.txt_MarqueVéhicule[0]":               marque,
                f"{px}.txt_TypeVarianteVersionVéhicule[0]":  type_variante,
                f"{px}.txt_GenreNational[0]":                genre_nat,
                f"{px}.txt_DénominationCommerciale[0]":      modele,
                f"{px}.num_DateImmatriculationJour[0]":      mec_j,
                f"{px}.num_DateImmatriculationMois[0]":      mec_m,
                f"{px}.num_DateImmatriculationAnnée[0]":     mec_a,
                f"{px}.num_KilométrageCompteur[0]":          km,
                f"{px}.num_Formule[0]":                      num_formule,
                # Vendeur
                f"{px}.txt_IdentitéVendeur[0]":             identite_vendeur,
                f"{px}.num_VoieAdresse[0]":                  vendeur_num_voie,
                f"{px}.txt_ExtensionAdresse[0]":             vendeur_ext,
                f"{px}.txt_TypeVoieAdresse[0]":              vendeur_type_voie,
                f"{px}.txt_NomVoie[0]":                      vendeur_nom_voie,
                f"{px}.num_CodePostalAdresse[0]":            vendeur_cp,
                f"{px}.txt_CommuneAdresse[0]":               vendeur_ville,
                # Date/heure cession
                f"{px}.num_DateVenteJour[0]":                vente_j,
                f"{px}.num_DateVenteMois[0]":                vente_m,
                f"{px}.num_DateVenteAnnée[0]":               vente_a,
                f"{px}.num_HoraireVente1[0]":                vente_h,
                f"{px}.num_HoraireVente2[0]":                vente_min,
                # Acheteur
                f"{px}.txt_IdentitéAcheteur[0]":            identite_acheteur,
                f"{px}.num_DateNaissanceAcheteurJ[0]":       acheteur_nais_j,
                f"{px}.num_DateNaissanceAcheteurM[0]":       acheteur_nais_m,
                f"{px}.num_DateNaissanceAcheteurA[0]":       acheteur_nais_a,
                f"{px}.txt_LieuNaissanceAcheteur[0]":        acheteur_nais_lieu,
                f"{px}.num_VoieAdresseAcheteur[0]":          acheteur_num_voie,
                f"{px}.txt_ExtensionAdresseAcheteur[0]":     acheteur_ext,
                f"{px}.txt_TypeVoieAdresseAcheteur[0]":      acheteur_type_voie,
                f"{px}.txt_NomVoieAdresseAcheteur[0]":       acheteur_nom_voie,
                f"{px}.num_CodePostalAdresseAcheteur[0]":    acheteur_cp,
                f"{px}.txt_CommuneAdresseAcheteur[0]":       acheteur_ville,
                # Lieux déclaration
                f"{px}.txt_LieuDéclaration1[0]":             lieu_cession,
                f"{px}.num_DateDéclaration[0]":              date_str,
                f"{px}.txt_LieuDéclaration2[0]":             lieu_cession,
                f"{px}.txt_dateDéclaration[0]":              date_str,
                # Radios
                f"{px}.Groupe_de_boutons_radio1[0]":         radio_ci,
                f"{px}.Groupe_de_boutons_radio2[0]":         radio_vendeur_sexe,
                f"{px}.Groupe_de_boutons_radio3[0]":         radio_vendeur_type,
                f"{px}.Groupe_de_boutons_radio4[0]":         radio_cession,
                f"{px}.Groupe_de_boutons_radio5[0]":         radio_acheteur_type,
                f"{px}.Groupe_de_boutons_radio6[0]":         radio_acheteur_sexe,
                # Cases à cocher
                f"{px}.ckb_ValidationDéclaration1[0]":       "/1",
                f"{px}.ckb_ValidationDéclaration2[0]":       "/1",
                f"{px}.ckb_ValidationDéclarationA1[0]":      "/1",
                f"{px}.ckb_ValidationDéclarationA2[0]":      "/1",
            })

        writer.update_page_form_field_values(writer.pages[0], fields, auto_regenerate=False)
        writer.update_page_form_field_values(writer.pages[1], fields, auto_regenerate=False)

        buffer = io.BytesIO()
        writer.write(buffer)
        buffer.seek(0)

        return send_file(buffer, mimetype="application/pdf",
                         as_attachment=True,
                         download_name=f"cerfa-cession-{immat}.pdf")
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
