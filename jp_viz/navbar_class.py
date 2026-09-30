from .models import ArticleLg


class Navbar:
    """
    Classe responsable de la génération des éléments de navigation (navbar)
    pour une langue donnée.
    """

    # -------------
    # Constructor
    # -------------
    def __init__(self, lg: str):
        self.nav_items = {}

        if not lg:
            return (
                "ERROR Navbar class initialization"  # pas de langue = pas de navigation
            )

        rows = (
            ArticleLg.objects.filter(language_code=lg)
            .exclude(nav__isnull=True)
            .values("id", "active", "nav", "art_slug")
        )

        self.nav_items = {
            row["active"]: {
                "id": row["id"],
                "active": row["active"],
                "nav": row["nav"],
                "slug": row["art_slug"],
            }
            for row in rows
        }

    def __str__(self):
        return "Navbar initialization"

    def to_json(self):
        return self.nav_items
