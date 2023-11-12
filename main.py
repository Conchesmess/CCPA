
from app import app
import os
import nltk

if __name__ == "__main__":
    
    os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'

    root = os.path.dirname(os.path.abspath(__file__))
    print(root)
    download_dir = os.path.join(root, 'nltk_data')
    print(download_dir)
    #os.chdir(download_dir)
    nltk.data.path.append(download_dir)
    
    # app.run(debug="True")
    app.run()