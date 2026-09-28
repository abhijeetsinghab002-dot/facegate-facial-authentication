# FaceGate — Web-Based Facial Authentication

A local Flask/OpenCV learning project with webcam enrollment, face matching, a blink liveness hint, session login, and rate limiting.

## Important limitation

This is an educational demonstration, not production biometric security. Haar cascades and a single blink challenge can be fooled. Production systems require audited face-recognition models, stronger liveness detection, encrypted biometric-template storage, consent/retention controls, HTTPS, CSRF protection, monitoring, and a non-biometric recovery method.

## Windows setup

1. Extract the ZIP.
2. Open the extracted `facial_auth_completed` folder in File Explorer.
3. Click the File Explorer address bar, type `cmd`, and press Enter.
4. Create a virtual environment:
   ```bat
   py -m venv .venv
   ```
5. Activate it:
   ```bat
   .venv\Scripts\activate
   ```
6. Install packages:
   ```bat
   py -m pip install -r requirements.txt
   ```
7. Run the tests:
   ```bat
   py -m unittest -v
   ```
8. Start the application:
   ```bat
   py app.py
   ```
9. Open `http://127.0.0.1:5000` in Chrome or Edge and allow camera access.

## Use

1. Select **Enroll**, enter a username, center one face, and click **Enroll face**.
2. Select **Log in**, use the same username, and click **Start login**.
3. Look at the camera for the first capture, then blink when prompted.

Only a compact numerical face template is saved under `instance/face_templates`. Raw webcam frames are discarded. The `instance/` directory is ignored by Git and must not be uploaded.

## GitHub upload

Upload the project files except `.venv/` and `instance/`. Those folders are already covered by `.gitignore`.
