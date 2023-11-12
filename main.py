
from app import app
import os
import nltk

if __name__ == "__main__":
    
    os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'

    download_dir = '/nltk_data'
    nltk.data.path.append(download_dir)
    
    app.run(debug="True")
    # app.run()