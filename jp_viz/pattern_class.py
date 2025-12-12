# PEP8
# flake8 /home/laurent/projects/django-web-app/jenniferperseverante_dev_site/jp_viz/pattern_class.py

from .models import ArticleLg


class Pattern:

    patterns = {
        '%%EMAIL%%': 'jennifer.perseverante@gmail.com',
        '%%PHONE%%': '(+33) 06.60.64.86.26',
        '%%FACEBOOK%%': 'https://www.facebook.com/jenniferperseverante/',
        '%%FACEBOOK-VIDEOS%%': 'https://www.facebook.com/jenniferperseverante/videos/',
        '%%INSTAGRAM%%': 'https://www.instagram.com/jenniferperseverante/',
        '%%YOUTUBE%%': 'https://www.youtube.com/channel/UCypPiuUYTPCPGUn5n_rXYcQ',
        # '%%STAR%%': '<img src="/static/images/star.png" style="display:inline" alt="star">',
        # '%%STAR2%%': '<img src="/static/images/star2.png" style="display:inline" alt="half star">',
        '%%STAR45%%': '<img src="/static/images/stars45.png" style="display:inline" alt="4.5 stars">',
        '%%STAR50%%': '<img src="/static/images/stars50.png" style="display:inline" alt="5 stars">',
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

            newValue = f'({slug})'

            self.text = self.text.replace(f'(Id:{id})', newValue)
            p1 = self.text.find('(Id:')
            i +=1

        return self.text


    # -------------------
    # Post Processing
    # -------------------
    def postProcess(self):
        # Replace patterns
        for pattern, value in self.patterns.items():
            self.text = self.text.replace(pattern, value)

        # Replace videos
        self.replaceVideos()

        return self.text

    # -------------------------------
    # <p>(Video:url)</p>
    # <p>(Video:https://www.youtube.com/embed/04cK7P0cuGE)</p>
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

            # Youtube video (Responsive by Bootstrap 4)
            elif url.find('https://www.youtube.com/embed') != -1:
                newValue = f'''
                <div class="embed-responsive embed-responsive-16by9">
                  <iframe
                    src="{url}"
                    title="Jennifer Perseverante"
                    referrerpolicy="strict-origin-when-cross-origin"
                    allowfullscreen>
                  </iframe>
                </div>'''

            # Facebook video
            elif url.find('https://www.facebook.com/') != -1:
                url2 = url.replace('/', '%2F').replace(':', '%3A')
                newValue = f'''
                <div class="embed-responsive embed-responsive-16by9">
                  <iframe 
                    src="https://www.facebook.com/plugins/video.php?href={url2}%2F&show_text=0"
                    width="100%"
                    style="border:none; overflow:hidden; width:100%; height:100%; position:absolute; top:0; left:0;"
                    scrolling="no"
                    frameborder="0"
                    allowfullscreen="true"
                    allow="autoplay; clipboard-write; encrypted-media; picture-in-picture; web-share">
                  </iframe>
                </div>            
                '''
            else:
                break  # End of loop

            self.text = self.text.replace(f'(Video:{url})', newValue)
            p1 = self.text.find('(Video:')
            i +=1

        return None