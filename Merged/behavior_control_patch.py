--- connection.py	Sun Oct 21 18:37:10 2018
+++ connection.py	Sun Oct 28 23:04:36 2018
@@ -252,6 +252,22 @@
         """
         return self._control_events.lost_event
 
+    # WV
+    @property
+    def control_granted_event(self) -> asyncio.Event:
+        """This provides an :class:`asyncio.Event` that a user may :func:`wait()` upon to
+        detect when Vector has taken control of the behaviors at a higher priority.
+
+        .. testcode::
+
+            import anki_vector
+
+            async def auto_reconnect(conn: anki_vector.connection.Connection):
+                await conn.control_granted_event.wait()
+                conn.request_control()
+        """
+        return self._control_events.granted_event        
+
     def request_control(self, timeout: float = 10.0):
         """Explicitly request control. Typically used after detecting :func:`control_lost_event`.
 
@@ -274,7 +290,8 @@
         except futures.TimeoutError as e:
             raise exceptions.VectorControlException(f"Surpassed timeout of {timeout}s") from e
 
-    def connect(self, timeout: float = 10.0) -> None:
+    # WV -- Add request_control parameter
+    def connect(self, timeout: float = 10.0, request_control: bool = True) -> None:
         """Connect to Vector. This will start the connection thread which handles all messages
         between Vector and Python.
 
@@ -299,7 +316,7 @@
         if self._thread:
             raise Exception("\n\nRepeated connections made to open Connection.")
         self._ready_signal.clear()
-        self._thread = threading.Thread(target=self._connect, args=(timeout,), daemon=True, name="gRPC Connection Handler Thread")
+        self._thread = threading.Thread(target=self._connect, args=(timeout,request_control,), daemon=True, name="gRPC Connection Handler Thread")
         self._thread.start()
         ready = self._ready_signal.wait(timeout=2 * timeout)
         if not ready:
@@ -309,7 +326,8 @@
             delattr(self._ready_signal, "exception")
             raise e
 
-    def _connect(self, timeout: float) -> None:
+    # WV -- Add request_control parameter
+    def _connect(self, timeout: float, request_control: bool) -> None:
         """The function that runs on the connection thread. This will connect to Vector,
         and establish the BehaviorControl stream.
         """
@@ -351,7 +369,9 @@
                 raise exceptions.VectorInvalidVersionException(version, protocol_version)
 
             self._control_stream_task = self._loop.create_task(self._open_connections())
-            self._loop.run_until_complete(self._request_control(timeout=timeout))
+            # WV -->--
+            if (request_control): self._loop.run_until_complete(self._request_control(timeout=timeout))
+            # WV --<--
         except Exception as e:  # pylint: disable=broad-except
             # Propagate the errors to the calling thread
             setattr(self._ready_signal, "exception", e)
--- robot.py	Sun Oct 21 18:37:10 2018
+++ robot.py	Sun Oct 28 22:25:40 2018
@@ -88,7 +88,9 @@
     :param enable_vision_mode: Turn on face detection.
     :param enable_camera_feed: Turn camera feed on/off.
     :param enable_audio_feed: Turn audio feed on/off.
-    :param show_viewer: Render camera feed on/off."""
+    :param show_viewer: Render camera feed on/off.
+    :param request_control: Requesting control on connection
+    """
 
     def __init__(self,
                  serial: str = None,
@@ -100,7 +102,8 @@
                  enable_vision_mode: bool = False,
                  enable_camera_feed: bool = False,
                  enable_audio_feed: bool = False,
-                 show_viewer: bool = False):
+                 show_viewer: bool = False,
+                 request_control: bool = True):
 
         if default_logging:
             util.setup_basic_logging()
@@ -165,6 +168,10 @@
         self._enable_audio_feed = enable_audio_feed
         self._show_viewer = show_viewer
 
+        # WV -->--
+        self._request_control = request_control
+        # WV --<--
+
     def _read_configuration(self, serial: str) -> dict:
         """Open the default conf file, and read it into a :class:`configparser.ConfigParser`
 
@@ -601,7 +608,7 @@
         :param timeout: The time to allow for a connection before a
             :class:`anki_vector.exceptions.VectorTimeoutException` is raised.
         """
-        self.conn.connect(timeout=timeout)
+        self.conn.connect(timeout=timeout, request_control=self._request_control)
         self.events.start(self.conn)
 
         # Initialize components
@@ -740,6 +747,10 @@
                                                    duration_scalar=duration_scalar)
         return await self.conn.grpc_interface.SayText(say_text_request)
 
+    @connection.on_connection_thread()
+    async def release_control(self) -> None:
+        release_request = protocol.BehaviorControlRequest(control_release=protocol.ControlRelease())        
+        self.conn.grpc_interface.BehaviorControl(release_request)            
 
 class AsyncRobot(Robot):
     """The AsyncRobot object is just like the Robot object, but allows multiple commands