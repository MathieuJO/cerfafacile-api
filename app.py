from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
from pypdf import PdfReader, PdfWriter
import os, io
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Autorise TOUS les domaines

CERFA_PATH = os.path.join(os.path.dirname(__file__), "cerfa.pdf")

@app.route("/")
def index():
    return "CerfaFacile API - OK"

@app.route("/generer-cerfa", methods=["POST"])
def generer_cerfa():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Données manquantes"}), 400

        vendeur_nom     = data.get("vendeur_nom", "").upper()
        vendeur_prenom  = data.get("vendeur_prenom", "")
        vendeur_adresse = data.get("vendeur_adresse", "")
        vendeur_cp      = data.get("vendeur_cp", "")
        vendeur_ville   = data.get("vendeur_ville", "")

        acheteur_nom     = data.get("acheteur_nom", "").upper()
        acheteur_prenom  = data.get("acheteur_prenom", "")
        acheteur_adresse = data.get("acheteur_adresse", "")
        acheteur_cp      = data.get("acheteur_cp", "")
        acheteur_ville   = data.get("acheteur_ville", "")

        immat  = data.get("immat", "").upper()
        marque = data.get("marque", "")
        modele = data.get("modele", "")
        km     = str(data.get("km", ""))

        # Date MEC
        date_mec = data.get("date_mec", "")
        try:
            d = datetime.strptime(date_mec, "%Y-%m-%d")
            mec_j = str(d.day).zfill(2)
            mec_m = str(d.month).zfill(2)
            mec_a = str(d.year)
        except:
            mec_j = mec_m = mec_a = ""

        # Date/heure cession
        now     = datetime.now()
        vente_j = str(now.day).zfill(2)
        vente_m = str(now.month).zfill(2)
        vente_a = str(now.year)
        heure1  = str(now.hour).zfill(2)
        heure2  = str(now.minute).zfill(2)
        date_str = now.strftime("%d/%m/%Y")

        # Décomposer adresse vendeur
        vendeur_num_voie = vendeur_type_voie = ""
        vendeur_nom_voie = vendeur_adresse
        parts = vendeur_adresse.split(" ", 1)
        if parts and parts[0].isdigit():
            vendeur_num_voie = parts[0]
            reste = parts[1] if len(parts) > 1 else ""
            mots  = reste.split(" ", 1)
            vendeur_type_voie = mots[0] if mots else ""
            vendeur_nom_voie  = mots[1] if len(mots) > 1 else reste

        # Décomposer adresse acheteur
        acheteur_num_voie = acheteur_type_voie = ""
        acheteur_nom_voie = acheteur_adresse
        parts2 = acheteur_adresse.split(" ", 1)
        if parts2 and parts2[0].isdigit():
            acheteur_num_voie = parts2[0]
            reste2 = parts2[1] if len(parts2) > 1 else ""
            mots2  = reste2.split(" ", 1)
            acheteur_type_voie = mots2[0] if mots2 else ""
            acheteur_nom_voie  = mots2[1] if len(mots2) > 1 else reste2

        reader = PdfReader(CERFA_PATH)
        writer = PdfWriter()
        writer.append(reader)

        fields = {}
        for p in [1, 2]:
            px = f"topmostSubform[0].Page{p}[0]"
            fields.update({
                f"{px}.num_Immatriculation[0]":              immat,
                f"{px}.txt_MarqueVéhicule[0]":               marque,
                f"{px}.txt_DénominationCommerciale[0]":      modele,
                f"{px}.num_DateImmatriculationJour[0]":      mec_j,
                f"{px}.num_DateImmatriculationMois[0]":      mec_m,
                f"{px}.num_DateImmatriculationAnnée[0]":     mec_a,
                f"{px}.num_KilométrageCompteur[0]":          km,
                f"{px}.txt_IdentitéVendeur[0]":              f"{vendeur_nom} {vendeur_prenom}",
                f"{px}.num_VoieAdresse[0]":                  vendeur_num_voie,
                f"{px}.txt_TypeVoieAdresse[0]":              vendeur_type_voie,
                f"{px}.txt_NomVoie[0]":                      vendeur_nom_voie,
                f"{px}.num_CodePostalAdresse[0]":            vendeur_cp,
                f"{px}.txt_CommuneAdresse[0]":               vendeur_ville,
                f"{px}.num_DateVenteJour[0]":                vente_j,
                f"{px}.num_DateVenteMois[0]":                vente_m,
                f"{px}.num_DateVenteAnnée[0]":               vente_a,
                f"{px}.num_HoraireVente1[0]":                heure1,
                f"{px}.num_HoraireVente2[0]":                heure2,
                f"{px}.txt_IdentitéAcheteur[0]":             f"{acheteur_nom} {acheteur_prenom}",
                f"{px}.num_VoieAdresseAcheteur[0]":          acheteur_num_voie,
                f"{px}.txt_TypeVoieAdresseAcheteur[0]":      acheteur_type_voie,
                f"{px}.txt_NomVoieAdresseAcheteur[0]":       acheteur_nom_voie,
                f"{px}.num_CodePostalAdresseAcheteur[0]":    acheteur_cp,
                f"{px}.txt_CommuneAdresseAcheteur[0]":       acheteur_ville,
                f"{px}.txt_LieuDéclaration1[0]":             vendeur_ville,
                f"{px}.num_DateDéclaration[0]":              date_str,
                f"{px}.txt_LieuDéclaration2[0]":             acheteur_ville,
                f"{px}.txt_dateDéclaration[0]":              date_str,
                f"{px}.Groupe_de_boutons_radio3[0]":         "/2",
                f"{px}.Groupe_de_boutons_radio5[0]":         "/2",
                f"{px}.Groupe_de_boutons_radio4[0]":         "/1",
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

        return send_file(
            buffer,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=f"cerfa-cession-{immat}.pdf"
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
