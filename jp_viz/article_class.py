from typing import Dict
from django.core.exceptions import ObjectDoesNotExist

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
    