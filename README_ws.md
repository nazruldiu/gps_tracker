Socket.IO bridge (Flask-SocketIO)
--------------------------------
The project now uses a Flask + Socket.IO bridge. Run the bridge with:

```bash
pip install flask flask-socketio eventlet python-socketio
python scripts/flask_ws.py
```

The bridge accepts two kinds of Socket.IO events:

- `get_gps` — client emits `{ imei: '...' }` to request current GPS/status for an IMEI; server responds with `gps_info`.
- `cast` — upstream services (Django) can connect as a Socket.IO client and emit `cast` objects; the bridge will re-broadcast received `cast` events to all connected browser clients.

Browser client example (uses Socket.IO client):

```html
<script src="https://cdn.socket.io/4.6.1/socket.io.min.js"></script>
<script>
  const socket = io('http://localhost:6791');
  socket.on('connect', () => console.log('connected'));
  socket.on('cast', cast => {
    console.log('cast', cast);
    // handle location/status as before
  });
  // request GPS for an IMEI
  socket.emit('get_gps', { imei: 'YOUR_IMEI' });
  socket.on('gps_info', msg => console.log('gps_info', msg));
</script>
```

See `scripts/flask_ws.py` for details and configuration (use the `SAPI_SOCKETIO_URL` Django setting from Django code to point to the bridge).
