from pipeline.google_workspace import pilier_nom, idea_to_idees_row


def test_pilier_nom():
    assert pilier_nom(1) == "IA appliquée"
    assert pilier_nom("5") == "Vision"
    assert pilier_nom(None) == ""
    assert pilier_nom(99) == ""


def test_idea_to_idees_row_mapping():
    idea = {"id": "idee-1", "pilier": 2, "titre": "Titre", "angle": "Angle",
            "confidentialite": "public",
            "source": {"type": "youtube", "chaine": "@x", "url": "u"}}
    row = idea_to_idees_row(idea, "2026-06-28", 1)
    assert row[0] == "2026-06-28-1"                              # id_idee
    assert row[1] == "2026-06-28"                                # date_creation
    assert row[2] == "youtube @x"                                # source
    assert row[3] == "Titre"                                     # idee_brute
    assert row[4] == "Angle"                                     # contexte
    assert row[5] == "Transformation numérique industrielle"     # theme
    assert row[8] == "public"                                    # confidentialite
    assert row[9] == "proposee"                                  # statut
    assert row[11] == "u"                                        # lien_ressource
    assert len(row) == 12
