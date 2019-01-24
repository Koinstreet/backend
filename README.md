Python Crypto WebSocket Server/Client

In order to run the socket, you need to navigate to the /ks_bend/run/ directory and run the appropriate shell script

• Python 2.7 (Unix) | chmod u+x py_install.sh && ./py_install.sh   (Pip)
• Python 3+  (Unix) | chmod u+x py3_install.sh && ./py3 install.sh (Pip3) 
• Windows           | pip install -r requirements.txt  or  pip3 install -r requirements.txt  
Navigate to your /ks_bend/server/ directory once you have those libraries in the scripts above installed. You will need to open and run ‘main.py’; this is the script which opens your localhost server and activates each socket connection.

In turn, the file ‘webapp.html’ contains javascript code contains a listener socket which recieves all messages from the localhost and displays them on a simple tabbed pane template in HTML. This file is located in /ks_bend/web_app/.

In total this websocket server is subscribing to 13 different connections asynchronusly and outputting all collected data as a localhost event.

Each websocket connection on Binance and Coinbase is able to mess up and reconnect up to three times. If limit is exceeded the script automatically breaks out of that task and does not reopen it. This design was placed to make sure exchange client code is up to date and working efficiently.
