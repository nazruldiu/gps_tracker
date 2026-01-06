from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Run the Flask-SocketIO bridge (scripts/flask_ws.py) from manage.py'

    def add_arguments(self, parser):
        parser.add_argument('--host', default='127.0.0.1', help='Host to bind')
        parser.add_argument('--port', type=int, default=6791, help='Port to listen on')
        parser.add_argument('--eventlet', action='store_true', help='Apply eventlet monkey patching')

    def handle(self, *args, **options):
        host = options['host']
        port = options['port']
        use_eventlet = options['eventlet']

        try:
            # import the bridge module
            import importlib
            fw = importlib.import_module('scripts.flask_ws')
        except Exception as e:
            msg = str(e)
            self.stderr.write(self.style.ERROR(f'Failed to import scripts.flask_ws: {msg}'))
            # give actionable hints for common missing deps
            if 'No module named' in msg or isinstance(e, ModuleNotFoundError):
                missing = None
                try:
                    # extract missing module name from message
                    missing = msg.split("No module named")[-1].strip().strip(" '")
                except Exception:
                    missing = None
                if missing:
                    self.stderr.write(self.style.WARNING(f"It looks like '{missing}' is not installed."))
                self.stderr.write(self.style.WARNING('Install required packages:'))
                self.stderr.write("  pip install flask flask-socketio python-socketio eventlet")
            return

        if use_eventlet:
            try:
                import eventlet
                eventlet.monkey_patch()
            except Exception:
                self.stderr.write(self.style.WARNING('eventlet not available; continuing without monkey patch'))

        self.stdout.write(self.style.SUCCESS(f'Starting Socket.IO bridge on {host}:{port}'))
        try:
            # fw.socketio and fw.app are defined in scripts/flask_ws.py
            fw.socketio.run(fw.app, host=host, port=port)
        except KeyboardInterrupt:
            self.stdout.write('Interrupted')
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Error running bridge: {e}'))
