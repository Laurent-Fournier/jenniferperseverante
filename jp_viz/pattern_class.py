# PEP8
# flake8 /home/laurent/projects/django-web-app/jenniferperseverante_dev_site/jp_viz/pattern_class.py

from jp_viz.models import ArticleLg


class Pattern:

    patterns = {
        '%%EMAIL%%': 'jennifer.perseverante@gmail.com',
        '%%PHONE%%': '(+33) 06.60.64.86.26',
        '%%FACEBOOK%%': 'https://www.facebook.com/jenniferperseverante/',
        '%%FACEBOOK-VIDEOS%%': 'https://www.facebook.com/jenniferperseverante/videos/',
        '%%INSTAGRAM%%': 'https://www.instagram.com/jenniferperseverante/',
        '%%YOUTUBE%%': 'https://www.youtube.com/channel/UCypPiuUYTPCPGUn5n_rXYcQ',
    }

    # -----------------------------------
    # Constructor
    # -----------------------------------
    def __init__(self, text, language_code):
        self.text = text
        self.language_code = language_code

    def __str__(self):
        return "Pattern processing"

    # -------------------
    # Pre Processing
    # -------------------
    def preProcess(self):
        p1 = self.text.find('(Id:')

        i=0
        while p1 != -1:
            if i>10:
                break

            p2 = self.text.find(')', p1+4)
            id = self.text[p1+4:p2]

            slug = (
                ArticleLg.objects
                .filter(id=id, language_code=self.language_code)
                .values_list('art_slug', flat=True)
                .first()
            ) or "ERROR"

            # slug = 'ERROR'
            # rows = ArticleLg.objects.raw(
            #     f'SELECT id, language_code, art_slug FROM article_lg WHERE id={id} AND language_code="{self.language_code}"'
            # )
            # for row in rows:
            #     slug = row.art_slug

            newValue = f'({slug})'

            self.text = self.text.replace(f'(Id:{id})', newValue)
            p1 = self.text.find('(Id:')
            i +=1

        return self.text


    # -------------------
    # Post Processing
    # -------------------
    def postProcess(self):
        for pattern, value in self.patterns.items():
            self.text = self.text.replace(pattern, value)

        self.replaceVideos()

        return self.text

    # -------------------------------
    # (Video:url Cover:src) TO DO
    # (Video:url)
    # (Video:https://www.youtube.com/embed/04cK7P0cuGE)
    # -------------------------------
    def replaceVideos(self):
        p1 = self.text.find('(Video:')
        
        i=0
        while p1 != -1:
            if i>10:
                break

            p2 = self.text.find(')', p1+7)
            url = self.text[p1+7:p2]

            # MP4 video
            newValue = ''
            if url.find('mp4') != -1:
                newValue = f'''
                <video controls>
                    <source src="{url}" type="video/mp4">
                    Your browser does not support the video tag.
                </video>'''

            # Youtube video
            elif url.find('https://www.youtube.com/embed') != -1:
                newValue = f'''
                <div class="video-container">
                <iframe src="{url}" 
                    title="Youtube video"
                    frameborder="0"
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                    allowfullscreen
                >
                </iframe>
                </div>                
                '''

            # Facebook video
            elif url.find('https://www.facebook.com/') != -1:
                url2 = url.replace('/', '%2F').replace(':', '%3A')
                newValue = f'''
                <div class="video-container">
                <iframe 
                    title="Facebook video"
                    src="https://www.facebook.com/plugins/video.php?href={url2}%2F&show_text=0" 
                    scrolling="no" frameborder="0" 
                    allowfullscreen="true" 
                    allow="autoplay; clipboard-write; encrypted-media; picture-in-picture; web-share" 
                >
                </iframe>
                </div>            
                '''
            else:
                break  # End of loop

            self.text = self.text.replace(f'(Video:{url})', newValue)
            p1 = self.text.find('(Video:')
            i +=1

        return None