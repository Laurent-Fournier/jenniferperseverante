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
            return 'ERROR Navbar class initialization' # pas de langue = pas de navigation
                
        rows = (
            ArticleLg.objects
            .filter(language_code=lg)
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
        
        # Add Specifics labels
        labels = {'fr': 'Prestations', 'en': 'Services', 'es': 'Servicios'}
        self.nav_items["services"] = { "id": None, "active": None, "nav": labels[lg], "slug": None}

        labels = {'fr': 'Contact', 'en': 'Contact Us', 'es': 'Contacto'}
        slugs  = {'fr': 'contact', 'en': 'contact-us', 'es': 'contacto'}
        self.nav_items["contact"] = { "id": None, "active": None, "nav": labels[lg], "slug": slugs[lg]}


    def __str__(self):
        return "Navbar initialization"


    def to_json(self):
        return self.nav_items