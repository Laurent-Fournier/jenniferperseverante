from typing import Dict
from django.core.exceptions import ObjectDoesNotExist
import locale
from datetime import date

from .models import ArticleLg

class ArticleService:
    def __str__(self):
        return "Utility class for managing articles"


    def get_slugs(self, article_id: int) -> Dict[str, str]:
        """
        Returns a dictionary {language_code: art_slug} for a given article.
        
        Args:
            article_id: ID of the article for which slugs are requested.
            
        Returns:
            Dictionary mapping each language code to its corresponding slug.

        Raises:
            ObjectDoesNotExist: If the article does not exist.            
        """
        if not isinstance(article_id, int) or article_id <= 0:
            raise ValueError("article_id must be a positive integer.")        
        
        rows = (
            ArticleLg.objects
            .filter(id=article_id)
            .values('language_code', 'art_slug')
        )
        
        if not rows:
            raise ObjectDoesNotExist(f"No article found with ID {article_id}.")
        
        return {row['language_code']: row['art_slug'] for row in rows}   

    
    def get_date_lg(self, date: date, language : str) -> str:
        """
        Formats a date as clear text according to the specified language.

        Args:
            date: Date object to format.
            language: Language code ('fr', 'en', 'es').

        Returns:
            str: Formatted date as clear text.

        Raises:
            ValueError: If the language is not supported.
        """
        if date is None:
            return None

        # Save the current locale
        old_locale = locale.getlocale(locale.LC_TIME)

        try:
            if language  == 'fr':
                # Set the locale to French
                locale.setlocale(locale.LC_TIME, 'fr_FR.UTF-8')
                day = date.day
                month = date.strftime("%B")
                year = date.year
                day_str = f"{day}er" if day == 1 else str(day)
                return f"Article mis en ligne le {day_str} {month} {year}"

            elif language  == 'en':
                # Set the locale to English
                locale.setlocale(locale.LC_TIME, 'en_US.UTF-8')
                return date.strftime("Article published online on %B %e, %Y").replace('  ', ' ')

            elif language  == 'es':
                # Set the locale to Spanish
                locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
                return date.strftime("Artículo publicado en línea el %d de %B de %Y")

            else:
                raise ValueError(f"Unsupported language: {language}")

        finally:
            # Always restore the original locale
            locale.setlocale(locale.LC_TIME, old_locale)
            

    def get_comments(self, article_id: int):
        article_id = article["id"]
       
        return {}

