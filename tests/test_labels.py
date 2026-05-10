"""Tests pour les fonctions utilitaires de const.py."""

from custom_components.mel_collecte.const import garbage_label, alert_label


class TestGarbageLabel:
    """Tests de garbage_label()."""

    def test_omr_returns_ordures_menageres_residuelles(self):
        """Le code 'omr' retourne le libellé complet."""
        assert garbage_label("omr") == "Ordures ménagères résiduelles"

    def test_dv_returns_dechets_verts(self):
        """Le code 'dv' retourne 'Déchets verts'."""
        assert garbage_label("dv") == "Déchets verts"

    def test_cs_returns_cartons_sacs(self):
        """Le code 'cs' retourne 'Cartons / sacs'."""
        assert garbage_label("cs") == "Cartons / sacs"

    def test_enc_returns_encombrants(self):
        """Le code 'enc' retourne 'Encombrants'."""
        assert garbage_label("enc") == "Encombrants"

    def test_bio_returns_biodechets(self):
        """Le code 'bio' retourne 'Biodéchets'."""
        assert garbage_label("bio") == "Biodéchets"

    def test_verre_returns_verre(self):
        """Le code 'verre' retourne 'Verre'."""
        assert garbage_label("verre") == "Verre"

    def test_text_returns_textiles(self):
        """Le code 'text' retourne 'Textiles'."""
        assert garbage_label("text") == "Textiles"

    def test_deee_returns_dechets_electroniques(self):
        """Le code 'deee' retourne 'Déchets électroniques'."""
        assert garbage_label("deee") == "Déchets électroniques"

    def test_pile_returns_piles_et_batteries(self):
        """Le code 'pile' retourne 'Piles et batteries'."""
        assert garbage_label("pile") == "Piles et batteries"

    def test_emb_returns_emballages_recyclables(self):
        """Le code 'emb' retourne 'Emballages recyclables'."""
        assert garbage_label("emb") == "Emballages recyclables"

    def test_unknown_code_uppercase_fallback(self):
        """Un code inconnu retourne le code en uppercase."""
        assert garbage_label("unknown") == "UNKNOWN"
        assert garbage_label("xyz") == "XYZ"
        assert garbage_label("123") == "123"

    def test_case_insensitive(self):
        """La fonction est insensible à la casse."""
        assert garbage_label("OMR") == "Ordures ménagères résiduelles"
        assert garbage_label("Dv") == "Déchets verts"
        assert garbage_label("BIO") == "Biodéchets"

    def test_empty_string_returns_empty_uppercase(self):
        """Une chaîne vide retourne une chaîne vide uppercase."""
        assert garbage_label("") == ""


class TestAlertLabel:
    """Tests de alert_label()."""

    def test_danger_returns_alert_emoji(self):
        """Le type 'danger' retourne avec emoji."""
        assert alert_label("danger") == "⚠️ Alerte"

    def test_warning_returns_avertissement_emoji(self):
        """Le type 'warning' retourne avec emoji."""
        assert alert_label("warning") == "⚡ Avertissement"

    def test_info_returns_information_emoji(self):
        """Le type 'info' retourne avec emoji."""
        assert alert_label("info") == "ℹ️ Information"

    def test_unknown_type_capitalize_fallback(self):
        """Un type inconnu retourne le type capitalize."""
        assert alert_label("unknown") == "Unknown"
        assert alert_label("test") == "Test"
        assert alert_label("OTHER") == "Other"

    def test_case_insensitive(self):
        """La fonction est insensible à la casse."""
        assert alert_label("DANGER") == "⚠️ Alerte"
        assert alert_label("Warning") == "⚡ Avertissement"
        assert alert_label("INFO") == "ℹ️ Information"
