from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
from pypdf import PdfReader, PdfWriter
import os, io, base64
from datetime import datetime
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.lib.utils import ImageReader
from pypdf import PdfReader as PR2

app = Flask(__name__)
CORS(app)

CERFA_PATH = os.path.join(os.path.dirname(__file__), "cerfa.pdf")

@app.route("/")
def index():
    return "CerfaExpress API - OK"

def b64_to_image_reader(b64_data):
    """Convertit une image base64 en ImageReader pour reportlab"""
    if not b64_data:
        return None
    if ',' in b64_data:
        b64_data = b64_data.split(',')[1]
    img_bytes = base64.b64decode(b64_data)
    return ImageReader(io.BytesIO(img_bytes))

def creer_overlay_signatures(sig_vendeur, sig_acheteur, page_width, page_height, page_type):
    """
    Crée un PDF overlay avec les signatures pour une page donnée.
    page_type: 'p1' (page 1: vendeur haut, acheteur bas) ou 'p2' (page 2: acheteur haut, vendeur bas)
    """
    packet = io.BytesIO()
    c = rl_canvas.Canvas(packet, pagesize=(page_width, page_height))

    # Zones de signature sur le Cerfa (coordonnées PDF, origine bas-gauche)
    # Page 1 : vendeur en haut (~y=290-340), acheteur en bas (~y=55-100)
    # Page 2 : acheteur en haut (~y=290-340), vendeur en bas (~y=55-100)

    if page_type == 'p1':
        zones = {
            'vendeur':  (310, 292, 245, 48),   # x, y_bas, largeur, hauteur
            'acheteur': (310, 55,  245, 42),
        }
    else:  # p2 - ordre inversé
        zones = {
            'acheteur': (310, 292, 245, 48),
            'vendeur':  (310, 55,  245, 42),
        }

    # Dessiner signature vendeur
    if sig_vendeur:
        img = b64_to_image_reader(sig_vendeur)
        if img:
            z = zones['vendeur']
            c.drawImage(img, z[0], z[1], width=z[2], height=z[3],
                       mask='auto', preserveAspectRatio=True)

    # Dessiner signature acheteur
    if sig_acheteur:
        img = b64_to_image_reader(sig_acheteur)
        if img:
            z = zones['acheteur']
            c.drawImage(img, z[0], z[1], width=z[2], height=z[3],
                       mask='auto', preserveAspectRatio=True)

    c.save()
    packet.seek(0)
    return packet

@app.route("/generer-cerfa", methods=["POST"])
def generer_cerfa():
    try:
        d = request.get_json()
        if not d:
            return jsonify({"error": "Données manquantes"}), 400

        def s(k): return str(d.get(k, "") or "").strip()

        # ── Données formulaire
        immat           = s("immat").upper()
        marque          = s("marque")
        modele          = s("modele")
        type_variante   = s("type_variante")
        genre_nat       = s("genre_national")
        vin             = s("vin")
        mec_j           = s("mec_j").zfill(2)
        mec_m           = s("mec_m").zfill(2)
        mec_a           = s("mec_a")
        km              = s("km")
        num_formule     = s("num_formule")

        vendeur_nom      = s("vendeur_nom").upper()
        vendeur_prenom   = s("vendeur_prenom")
        vendeur_num_voie = s("vendeur_num_voie")
        vendeur_ext      = s("vendeur_ext")
        vendeur_tvoie    = s("vendeur_type_voie")
        vendeur_nvoie    = s("vendeur_nom_voie")
        vendeur_cp       = s("vendeur_cp")
        vendeur_ville    = s("vendeur_ville")
        vendeur_type     = s("vendeur_type")
        vendeur_sexe     = s("vendeur_sexe")

        acheteur_nom      = s("acheteur_nom").upper()
        acheteur_prenom   = s("acheteur_prenom")
        acheteur_nais_j   = s("acheteur_nais_j").zfill(2)
        acheteur_nais_m   = s("acheteur_nais_m").zfill(2)
        acheteur_nais_a   = s("acheteur_nais_a")
        acheteur_nais_lieu= s("acheteur_nais_lieu")
        acheteur_num_voie = s("acheteur_num_voie")
        acheteur_ext      = s("acheteur_ext")
        acheteur_tvoie    = s("acheteur_type_voie")
        acheteur_nvoie    = s("acheteur_nom_voie")
        acheteur_cp       = s("acheteur_cp")
        acheteur_ville    = s("acheteur_ville")
        acheteur_type     = s("acheteur_type")
        acheteur_sexe     = s("acheteur_sexe")

        type_cession = s("type_cession")
        vente_j      = s("vente_j").zfill(2)
        vente_m      = s("vente_m").zfill(2)
        vente_a      = s("vente_a")
        vente_h      = s("vente_h").zfill(2)
        vente_min    = s("vente_min").zfill(2)
        lieu_cession = s("lieu_cession")
        date_str     = f"{vente_j}/{vente_m}/{vente_a}"

        # Signatures
        sig_vendeur  = d.get("signature_vendeur")
        sig_acheteur = d.get("signature_acheteur")

        # Radios
        radio_vendeur_type  = "/2" if vendeur_type == "physique" else "/1"
        radio_vendeur_sexe  = "/1" if vendeur_sexe == "M" else "/2"
        radio_acheteur_type = "/2" if acheteur_type == "physique" else "/1"
        radio_acheteur_sexe = "/1" if acheteur_sexe == "M" else "/2"
        radio_cession = "/1" if type_cession == "ceder" else "/2"
        radio_ci = "/1" if s("ci_present") == "oui" else "/2"

        # ── Étape 1 : Remplir les champs texte du Cerfa
        reader = PdfReader(CERFA_PATH)
        writer = PdfWriter()
        writer.append(reader)

        fields = {}
        for p in [1, 2]:
            px = f"topmostSubform[0].Page{p}[0]"
            fields.update({
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
                f"{px}.txt_IdentitéVendeur[0]":              f"{vendeur_nom} {vendeur_prenom}",
                f"{px}.num_VoieAdresse[0]":                  vendeur_num_voie,
                f"{px}.txt_ExtensionAdresse[0]":             vendeur_ext,
                f"{px}.txt_TypeVoieAdresse[0]":              vendeur_tvoie,
                f"{px}.txt_NomVoie[0]":                      vendeur_nvoie,
                f"{px}.num_CodePostalAdresse[0]":            vendeur_cp,
                f"{px}.txt_CommuneAdresse[0]":               vendeur_ville,
                f"{px}.num_DateVenteJour[0]":                vente_j,
                f"{px}.num_DateVenteMois[0]":                vente_m,
                f"{px}.num_DateVenteAnnée[0]":               vente_a,
                f"{px}.num_HoraireVente1[0]":                vente_h,
                f"{px}.num_HoraireVente2[0]":                vente_min,
                f"{px}.txt_IdentitéAcheteur[0]":             f"{acheteur_nom} {acheteur_prenom}",
                f"{px}.num_DateNaissanceAcheteurJ[0]":       acheteur_nais_j,
                f"{px}.num_DateNaissanceAcheteurM[0]":       acheteur_nais_m,
                f"{px}.num_DateNaissanceAcheteurA[0]":       acheteur_nais_a,
                f"{px}.txt_LieuNaissanceAcheteur[0]":        acheteur_nais_lieu,
                f"{px}.num_VoieAdresseAcheteur[0]":          acheteur_num_voie,
                f"{px}.txt_ExtensionAdresseAcheteur[0]":     acheteur_ext,
                f"{px}.txt_TypeVoieAdresseAcheteur[0]":      acheteur_tvoie,
                f"{px}.txt_NomVoieAdresseAcheteur[0]":       acheteur_nvoie,
                f"{px}.num_CodePostalAdresseAcheteur[0]":    acheteur_cp,
                f"{px}.txt_CommuneAdresseAcheteur[0]":       acheteur_ville,
                f"{px}.txt_LieuDéclaration1[0]":             lieu_cession,
                f"{px}.num_DateDéclaration[0]":              date_str,
                f"{px}.txt_LieuDéclaration2[0]":             lieu_cession,
                f"{px}.txt_dateDéclaration[0]":              date_str,
                f"{px}.Groupe_de_boutons_radio1[0]":         radio_ci,
                f"{px}.Groupe_de_boutons_radio2[0]":         radio_vendeur_sexe,
                f"{px}.Groupe_de_boutons_radio3[0]":         radio_vendeur_type,
                f"{px}.Groupe_de_boutons_radio4[0]":         radio_cession,
                f"{px}.Groupe_de_boutons_radio5[0]":         radio_acheteur_type,
                f"{px}.Groupe_de_boutons_radio6[0]":         radio_acheteur_sexe,
                f"{px}.ckb_ValidationDéclaration1[0]":       "/1",
                f"{px}.ckb_ValidationDéclaration2[0]":       "/1",
                f"{px}.ckb_ValidationDéclarationA1[0]":      "/1",
                f"{px}.ckb_ValidationDéclarationA2[0]":      "/1",
            })

        writer.update_page_form_field_values(writer.pages[0], fields, auto_regenerate=False)
        writer.update_page_form_field_values(writer.pages[1], fields, auto_regenerate=False)

        # ── Étape 2 : Aplatir le PDF (flatten) pour rendre les champs permanents
        tmp1 = io.BytesIO()
        writer.write(tmp1)
        tmp1.seek(0)

        # ── Étape 3 : Injecter les signatures par overlay si présentes
        if sig_vendeur or sig_acheteur:
            reader2 = PR2(tmp1)
            writer2 = PdfWriter()

            for page_idx, page in enumerate(reader2.pages):
                mb = page.mediabox
                W, H = float(mb.width), float(mb.height)
                page_type = 'p1' if page_idx == 0 else 'p2'

                # Créer l'overlay signature pour cette page
                overlay_buf = creer_overlay_signatures(
                    sig_vendeur, sig_acheteur, W, H, page_type
                )

                # Fusionner avec la page originale
                overlay_reader = PR2(overlay_buf)
                overlay_page   = overlay_reader.pages[0]
                page.merge_page(overlay_page)
                writer2.add_page(page)

            buffer = io.BytesIO()
            writer2.write(buffer)
            buffer.seek(0)
            fname = f"cerfa-cession-{immat}-signe.pdf"
        else:
            buffer = tmp1
            fname  = f"cerfa-cession-{immat}.pdf"

        return send_file(buffer, mimetype="application/pdf",
                        as_attachment=True, download_name=fname)

    except Exception as e:
        import traceback
        return jsonify({"error": str(e), "trace": traceback.format_exc()}), 500


if __name__ == "__main__":
    app.run(debug=True)
