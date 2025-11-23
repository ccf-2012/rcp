# -*- coding: utf-8 -*-
import http.server
import socketserver
import json
import logging
from rcp_core import run_rcp_process, load_config, delete_links, execute_hardlinking, translate_path_to_agent_path

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

PORT = 6008 # We can make this configurable later

class RcpRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        # For now, we only have one endpoint, but we can add more later
        if self.path.startswith('/rcp/'):
            try:
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                payload = json.loads(post_data)

                logging.info(f"Received request on {self.path} with payload: {payload}")

                # Route to different handlers based on path
                if self.path == '/rcp/process':
                    self.handle_process(payload)
                elif self.path == '/rcp/relink':
                    # Placeholder for future implementation
                    self.handle_relink(payload)
                elif self.path == '/rcp/modify':
                    # Placeholder for future implementation
                    self.handle_modify(payload)
                elif self.path == '/rcp/delete_files':
                    self.handle_delete_files(payload)
                else:
                    self._send_response(404, {'status': 'error', 'message': 'Endpoint not found'})

            except json.JSONDecodeError:
                self._send_response(400, {'status': 'error', 'message': 'Invalid JSON payload.'})
            except Exception as e:
                logging.error(f"Error processing request: {e}", exc_info=True)
                self._send_response(500, {'status': 'error', 'message': str(e)})
        else:
            self._send_response(404, {'status': 'error', 'message': 'Not Found'})

    def handle_process(self, payload):
        """Handles the original processing request."""
        tor_path = payload.get('tor_path')
        torhash = payload.get('torhash')
        dl_uuid = payload.get('dl_uuid')
        torname = payload.get('torname')

        if not tor_path or not torhash:
            self._send_response(400, {'status': 'error', 'message': 'Missing tor_path or torhash for /rcp/process'})
            return

        run_rcp_process(
            tor_path=tor_path,
            torhash=torhash,
            dl_uuid=dl_uuid,
            torname=torname
        )
        self._send_response(200, {'status': 'success', 'message': 'Process completed successfully.'})

    def handle_relink(self, payload):
        """Handles relinking an existing media item."""
        logging.info("Handling /rcp/relink")
        self._handle_relink_request(payload)

    def handle_modify(self, payload):
        """Handles modifying a media item (delete old + create new)."""
        logging.info("Handling /rcp/modify")
        self._handle_relink_request(payload)

    def handle_delete_files(self, payload):
        """
        Handles deleting hardlinked files/folders on the agent.
        """
        logging.info("Handling /rcp/delete_files")
        rel_path = payload.get('rel_path')

        if not rel_path:
            self._send_response(400, {'status': 'error', 'message': 'Missing rel_path for /rcp/delete_files'})
            return

        config = load_config()
        try:
            delete_links(config, rel_path)
            self._send_response(200, {'status': 'success', 'message': f'Successfully deleted {rel_path}'})
        except Exception as e:
            logging.error(f"Error deleting files for {rel_path}: {e}", exc_info=True)
            self._send_response(500, {'status': 'error', 'message': str(e)})

    def _handle_relink_request(self, payload):
        """Core logic for both relink and modify operations."""
        old_rel_path = payload.get('old_rel_path')
        new_media_info = payload.get('new_media_info')
        tor_path = payload.get('tor_path')

        if not new_media_info or not tor_path:
            self._send_response(400, {'status': 'error', 'message': 'Missing new_media_info or tor_path'})
            return

        config = load_config()

        # 1. Delete old links if path is provided
        if old_rel_path:
            delete_links(config, old_rel_path)
        else:
            logging.info("No old_rel_path provided, skipping deletion.")

        # Translate the path before creating new links
        translated_tor_path = translate_path_to_agent_path(tor_path, config.get('path_mapping', {}))
        logging.info(f"Original tor_path: {tor_path}, Translated tor_path: {translated_tor_path}")

        # 2. Create new links
        execute_hardlinking(config, new_media_info, translated_tor_path)
        
        self._send_response(200, {'status': 'success', 'message': 'Relink process completed successfully.'})


    def _send_response(self, status_code, content_dict):
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(content_dict).encode('utf-8'))

def main():
    try:
        # Load config to ensure it's valid on startup
        load_config()
        
        with socketserver.TCPServer(("", PORT), RcpRequestHandler) as httpd:
            logging.info(f"RCP Agent starting on port {PORT}...")
            logging.info("Available endpoints: POST /rcp/process, POST /rcp/relink, POST /rcp/modify, POST /rcp/delete_files")
            httpd.serve_forever()
    except FileNotFoundError as e:
        logging.error(f"Could not start agent: {e}")
    except KeyError as e:
        logging.error(f"Could not start agent due to configuration error: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}", exc_info=True)

if __name__ == "__main__":
    main()
