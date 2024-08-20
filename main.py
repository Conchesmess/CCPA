
from app import app
import os

if __name__ == "__main__":
    
    os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'
    os.environ['islocal'] = "false"
    app.run(debug="True")
    # app.run()