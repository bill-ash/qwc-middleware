from pyqwc.pyqwc import start_server

# Starts the soap service WebConnector will connect with:
# - get_client_version 
# - authenticate 
# - check for new work (tickets)
# - process qbxml
# - return results if successful  

start_server()