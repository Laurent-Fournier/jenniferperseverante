#!/usr/bin/env python
"""
Description : Copy file from dev to UAT or PROD environement
Usage : 
cd ~/www/jpdev_site/
source env/bin/activate
python scripts/deliver.py --target=UAT
python scripts/deliver.py --target=PROD
"""

import shutil
import os
import argparse


def copyFile(filename, source_path, dest_path, patterns):
    print(f"Copy file: {source_path}/{filename} -> {dest_path}/{filename}")
    
    # Read source file
    with open(f"{source_path}/{filename}", "r", encoding="utf-8") as file:
        content = file.read()
        
    # Update the content
    if patterns is not None:
        for k,v in patterns.items():
            content = content.replace(k, v)
        
    # write destination file
    with open(f"{dest_path}/{filename}", "w", encoding="utf-8") as file:
        file.write(content)    

def copyDirectory(directory, source_path, dest_path):
    print(f"Copy dir: {source_path}/{directory} -> {dest_path}/{directory}")
    shutil.copytree(f"{source_path}/{directory}", f"{dest_path}/{directory}", dirs_exist_ok=True)



def main():
    parser = argparse.ArgumentParser(description="Copy files from DEV to UAT/PROD Django environnement.")
    parser.add_argument("--target", help="Target Django environment (UAT or PROD)", required=True)

    args = parser.parse_args()
    print(f"Target : {args.target}")
    
    current_path = os.getcwd()
    print(f"Current path : {current_path}")

    if args.target=='UAT':
        destination_path = os.path.dirname(current_path)+'/jpuat_site'
        patterns = {
            "ENVIRONMENT=DEV": "ENVIRONMENT=UAT",
            "jpdev_site": "jpuat_site",
            
            "DEBUG = True": "DEBUG = False",
            f"django-insecure-3m(80%z6rm7kus57n^t@!e7#dr8345&_rdt^iz9)+k8yn52^k)": f"django-insecure-0+o_iq_rum-=md-&5&&&xv)jxc!z%^tw=d^=v#$c5_y7uo29l-",
            "jp-dev.beautifuldata.fr": "jp-uat.beautifuldata.fr",
        }
    elif args.target=='PROD':
        destination_path = os.path.dirname(current_path)+'/jpprd_site'
        patterns = {
            "ENVIRONMENT=DEV": "ENVIRONMENT=PROD",
            "jpdev_site": "jpprd_site",

            "DEBUG = True": "DEBUG = True",  # TEMP
            f"django-insecure-3m(80%z6rm7kus57n^t@!e7#dr8345&_rdt^iz9)+k8yn52^k)": f"django-insecure-%4le6o9&x=+uzp@pzum7@mnr_y0dqo)8e0@26!a1+$4zh5xm16",
            "jp-dev.beautifuldata.fr": "jp-prod.beautifuldata.fr",
        }
    else:
        print(f"[ERROR] Bad Target: {args.target}")
        quit()
    print(f"Destination path : {destination_path}")
    

    # .env
    copyFile('.env', current_path, destination_path, patterns)
    
    # settings.py
    copyFile('jp_site/settings.py', current_path, destination_path, patterns)
    
    # urls.py
    copyFile('jp_site/urls.py', current_path, destination_path, None)

    # Views
    copyFile('jp_viz/contact_class.py', current_path, destination_path, None)
    copyFile('jp_viz/models.py', current_path, destination_path, None)
    copyFile('jp_viz/navbar_class.py', current_path, destination_path, None)
    copyFile('jp_viz/pattern_class.py', current_path, destination_path, None)
    copyFile('jp_viz/views.py', current_path, destination_path, None)
    copyFile('jp_viz/views_article.py', current_path, destination_path, None)
    copyFile('jp_viz/views_contact.py', current_path, destination_path, None)
    copyFile('jp_viz/views_gallery.py', current_path, destination_path, None)
    copyFile('jp_viz/views_media.py', current_path, destination_path, None)

    # Templates
    copyDirectory('jp_viz/templates', current_path, destination_path)

    # Static files
    copyDirectory('staticfiles', current_path, destination_path)


    print('✅ Delivery successfull!')

if __name__ == "__main__":
    main()