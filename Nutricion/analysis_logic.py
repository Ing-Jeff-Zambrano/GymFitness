import cv2
import mediapipe as mp
import numpy as np
import time

# --- 1. Inicialización de MediaPipe Pose (Global para todas las funciones) ---
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils

# Se inicializa 'pose' una sola vez.
# Reducimos un poco la confianza para intentar detectar más, pero ajusta si necesitas más precisión.
pose = mp_pose.Pose(min_detection_confidence=0.2, min_tracking_confidence=0.2)


# --- 2. Función Utilidad: Cálculo de Ángulo ---
def calculate_angle(a, b, c):
    """
    Calcula el ángulo en grados entre tres puntos (a, b, c),
    donde 'b' es el vértice del ángulo.
    """
    a = np.array(a)
    b = np.array(b)
    c = np.array(c)

    radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - np.arctan2(a[1] - b[1], a[0] - b[0])
    angle = np.abs(radians * 180.0 / np.pi)

    if angle > 180.0:
        angle = 360 - angle
    return angle


# --- FUNCIONES DE ANALISIS PARA CADA EJERCICIO ---

# ANALISIS DEL CURL DE BICEPS
def analyze_curl_biceps(video_path):
    # Parámetros del ejercicio (Ajusta estos valores según tu forma y encuadre)
    MIN_ELBOW_ANGLE_DOWN = 160  # Ángulo mínimo del codo cuando el brazo está extendido (abajo)
    MAX_ELBOW_ANGLE_UP = 60  # Ángulo máximo del codo cuando el brazo está contraído (arriba)

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return {"exercise": "Curl de Biceps", "total_reps_done": 0, "good_form_reps_count": 0, "effectiveness_percentage": 0.0,
                "feedback": "Error: No se pudo abrir el video para Curl de Bíceps."}

    reps = 0
    good_reps_count = 0
    current_stage = "abajo"
    rep_error_detected = False # Inicialización estandarizada

    print(f"--- Iniciando análisis de Curl de Bíceps para {video_path} ---") # Debug print

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image_rgb.flags.writeable = False
        results = pose.process(image_rgb)
        image_rgb.flags.writeable = True

        if results.pose_landmarks:
            landmarks = results.pose_landmarks.landmark
            try:
                # Coordenadas de las articulaciones del brazo (derecho e izquierdo)
                r_shoulder = [landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER].x,
                              landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER].y]
                r_elbow = [landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW].x, landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW].y]
                r_wrist = [landmarks[mp_pose.PoseLandmark.RIGHT_WRIST].x, landmarks[mp_pose.PoseLandmark.RIGHT_WRIST].y]

                l_shoulder = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER].x,
                              landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER].y]
                l_elbow = [landmarks[mp_pose.PoseLandmark.LEFT_ELBOW].x, landmarks[mp_pose.PoseLandmark.LEFT_ELBOW].y]
                l_wrist = [landmarks[mp_pose.PoseLandmark.LEFT_WRIST].x, landmarks[mp_pose.PoseLandmark.LEFT_WRIST].y]

                # Cálculo de Ángulos (promedio de ambos brazos)
                right_elbow_angle = calculate_angle(r_shoulder, r_elbow, r_wrist)
                left_elbow_angle = calculate_angle(l_shoulder, l_elbow, l_wrist)
                avg_elbow_angle = (right_elbow_angle + left_elbow_angle) / 2

                # --- DEBUG PRINT ---
                print(f"Etapa: {current_stage}, Ángulo Codo: {avg_elbow_angle:.1f}")
                # --- FIN DEBUG PRINT ---

                # Lógica de Conteo de Repeticiones y Etapa del Movimiento
                if avg_elbow_angle < MAX_ELBOW_ANGLE_UP:  # Brazo arriba (contraído)
                    if current_stage == "abajo" or current_stage == "bajando":
                        current_stage = "subiendo"
                    elif current_stage == "subiendo":
                        current_stage = "arriba"

                if avg_elbow_angle > MIN_ELBOW_ANGLE_DOWN:  # Brazo abajo (extendido)
                    if current_stage == "arriba" or current_stage == "subiendo":
                        current_stage = "bajando"
                    elif current_stage == "bajando":
                        reps += 1
                        if not rep_error_detected:
                            good_reps_count += 1
                            print(f"DEBUG: Repetición {reps} CONTADA (Buena Forma).") # Explicit good rep
                        else:
                            print(f"DEBUG: Repetición {reps} CONTADA (Forma Incorrecta - ROM).") # Explicit bad rep
                        rep_error_detected = False  # Resetear el flag de error
                        current_stage = "abajo"

                # Reglas de Corrección de Postura (afectan penalización por ROM)
                if current_stage == "subiendo" and avg_elbow_angle > MAX_ELBOW_ANGLE_UP + 10:
                    rep_error_detected = True
                    # print(f"DEBUG: Error ROM - No sube lo suficiente (Codo: {avg_elbow_angle:.1f})") # Debug print
                elif current_stage == "bajando" and avg_elbow_angle < MIN_ELBOW_ANGLE_DOWN - 10:
                    rep_error_detected = True
                    # print(f"DEBUG: Error ROM - No extiende lo suficiente (Codo: {avg_elbow_angle:.1f})") # Debug print
            except Exception as e:
                print(f"Error en landmarks para Curl de Bíceps (frame actual): {e}") # Debug print
                rep_error_detected = True  # Marca como error si hay problemas de detección
        else:
            rep_error_detected = True  # No hay landmarks detectados
            print("DEBUG: No se detectaron landmarks en el frame.") # Debug print

    cap.release()
    effectiveness = (good_reps_count / reps * 100) if reps > 0 else 100

    print(f"--- Análisis finalizado para Curl de Bíceps. Reps Totales: {reps}, Reps Buenas: {good_reps_count}, Efectividad: {effectiveness:.1f}% ---") # Debug print

    feedback = ""
    if reps == 0 and rep_error_detected: # Usar rep_error_detected
        feedback = "No se detectaron repeticiones o hubo problemas de detección. Asegúrate de estar bien encuadrado y con buena iluminación. Ajusta los umbrales si es necesario."
    elif reps > 0:
        feedback = f"Curl de Bíceps analizado: Realizaste {reps} repeticiones en total, con {good_reps_count} repeticiones de buena forma (ROM). Tu efectividad fue del {round(effectiveness, 1)}%. ¡Excelente progreso!"
        if effectiveness < 100:
            feedback += " Considera revisar tu rango de movimiento completo y el control del peso. Asegúrate de extender y flexionar completamente los codos."
    else:
        feedback = "No se detectaron repeticiones. ¿Realizaste el ejercicio correctamente? Asegúrate de que el movimiento del codo cruza los umbrales definidos y que la cámara te ve de lado."

    return {
        "exercise": "Curl de Biceps",
        "total_reps_done": reps, # Nueva clave
        "good_form_reps_count": good_reps_count, # Nueva clave
        "effectiveness_percentage": round(effectiveness, 1),
        "feedback": feedback
    }


# ANALISIS DE EXTENSIONES DE TRÍCEPS
def analyze_extensiones_triceps(video_path):
    # Parámetros del ejercicio (Ajusta estos valores)
    MIN_ELBOW_ANGLE_UP = 160  # Ángulo del codo cuando el brazo está extendido (arriba, al final del movimiento)
    MAX_ELBOW_ANGLE_DOWN = 90  # Ángulo del codo cuando el brazo está flexionado (abajo, al inicio del movimiento)

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return {"exercise": "Extensiones de Tríceps", "total_reps_done": 0, "good_form_reps_count": 0, "effectiveness_percentage": 0.0,
                "feedback": "Error: No se pudo abrir el video para Extensiones de Tríceps."}

    reps = 0
    good_reps_count = 0
    current_stage = "arriba"  # "arriba" o "abajo"
    rep_error_detected = False # Inicialización estandarizada

    print(f"--- Iniciando análisis de Extensiones de Tríceps para {video_path} ---") # Debug print

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image_rgb.flags.writeable = False
        results = pose.process(image_rgb)
        image_rgb.flags.writeable = True

        if results.pose_landmarks:
            landmarks = results.pose_landmarks.landmark
            try:
                # Coordenadas de las articulaciones del brazo
                r_shoulder = [landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER].x,
                              landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER].y]
                r_elbow = [landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW].x, landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW].y]
                r_wrist = [landmarks[mp_pose.PoseLandmark.RIGHT_WRIST].x, landmarks[mp_pose.PoseLandmark.RIGHT_WRIST].y]

                l_shoulder = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER].x,
                              landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER].y]
                l_elbow = [landmarks[mp_pose.PoseLandmark.LEFT_ELBOW].x, landmarks[mp_pose.PoseLandmark.LEFT_ELBOW].y]
                l_wrist = [landmarks[mp_pose.PoseLandmark.LEFT_WRIST].x, landmarks[mp_pose.PoseLandmark.LEFT_WRIST].y]

                # Cálculo de Ángulos (promedio de ambos brazos)
                right_elbow_angle = calculate_angle(r_shoulder, r_elbow, r_wrist)
                left_elbow_angle = calculate_angle(l_shoulder, l_elbow, l_wrist)
                avg_elbow_angle = (right_elbow_angle + left_elbow_angle) / 2

                # --- DEBUG PRINT ---
                print(f"Etapa: {current_stage}, Ángulo Codo: {avg_elbow_angle:.1f}")
                # --- FIN DEBUG PRINT ---

                # Lógica de Conteo de Repeticiones y Etapa del Movimiento
                if avg_elbow_angle < MAX_ELBOW_ANGLE_DOWN:  # Brazo flexionado (abajo)
                    if current_stage == "arriba" or current_stage == "subiendo":
                        current_stage = "bajando"
                    elif current_stage == "bajando":
                        current_stage = "abajo"

                if avg_elbow_angle > MIN_ELBOW_ANGLE_UP:  # Brazo extendido (arriba)
                    if current_stage == "abajo" or current_stage == "bajando":
                        current_stage = "subiendo"
                    elif current_stage == "subiendo":
                        reps += 1
                        if not rep_error_detected:
                            good_reps_count += 1
                            print(f"DEBUG: Repetición {reps} CONTADA (Buena Forma).") # Explicit good rep
                        else:
                            print(f"DEBUG: Repetición {reps} CONTADA (Forma Incorrecta - ROM).") # Explicit bad rep
                        rep_error_detected = False
                        current_stage = "arriba"

                # Reglas de Corrección de Postura (afectan penalización por ROM)
                if current_stage == "bajando" and avg_elbow_angle > MAX_ELBOW_ANGLE_DOWN + 10:
                    rep_error_detected = True
                    # print(f"DEBUG: Error ROM - No flexiona lo suficiente (Codo: {avg_elbow_angle:.1f})") # Debug print
                elif current_stage == "subiendo" and avg_elbow_angle < MIN_ELBOW_ANGLE_UP - 10:
                    rep_error_detected = True
                    # print(f"DEBUG: Error ROM - No extiende lo suficiente (Codo: {avg_elbow_angle:.1f})") # Debug print
            except Exception as e:
                print(f"Error en landmarks para Extensiones de Tríceps (frame actual): {e}") # Debug print
                rep_error_detected = True
        else:
            rep_error_detected = True
            print("DEBUG: No se detectaron landmarks en el frame.") # Debug print

    cap.release()
    effectiveness = (good_reps_count / reps * 100) if reps > 0 else 100

    print(f"--- Análisis finalizado para Extensiones de Tríceps. Reps Totales: {reps}, Reps Buenas: {good_reps_count}, Efectividad: {effectiveness:.1f}% ---") # Debug print

    feedback = ""
    if reps == 0 and rep_error_detected: # Usar rep_error_detected
        feedback = "No se detectaron repeticiones o hubo problemas de detección. Asegúrate de estar bien encuadrado y con buena iluminación. Ajusta los umbrales si es necesario."
    elif reps > 0:
        feedback = f"Extensiones de Tríceps analizadas: Realizaste {reps} repeticiones en total, con {good_reps_count} repeticiones de buena forma (ROM). Tu efectividad fue del {round(effectiveness, 1)}%. ¡Sigue así!"
        if effectiveness < 100:
            feedback += " Considera revisar tu rango de movimiento completo, extendiendo completamente arriba y flexionando al máximo."
    else:
        feedback = "No se detectaron repeticiones. ¿Realizaste el ejercicio correctamente? Asegúrate de que el movimiento del codo cruza los umbrales definidos y que la cámara te ve de lado."

    return {
        "exercise": "Extensiones de Tríceps",
        "total_reps_done": reps, # Nueva clave
        "good_form_reps_count": good_reps_count, # Nueva clave
        "effectiveness_percentage": round(effectiveness, 1),
        "feedback": feedback
    }


# ANALISIS DE PRESS DE HOMBROS
def analyze_press_hombros(video_path):
    # Parámetros del ejercicio (Ajusta estos valores)
    MIN_ELBOW_ANGLE_EXTENDED = 160  # Ángulo mínimo del codo cuando el brazo está extendido (arriba del todo)
    MAX_ELBOW_ANGLE_RACK = 100  # Ángulo máximo del codo cuando la barra está en la posición inicial (altura de hombros, codos flexionados)

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return {"exercise": "Press de Hombros", "total_reps_done": 0, "good_form_reps_count": 0, "effectiveness_percentage": 0.0,
                "feedback": "Error: No se pudo abrir el video para Press de Hombros."}

    reps = 0
    good_reps_count = 0
    current_stage = "abajo"  # Etapa inicial: barra en posición de rack (altura de hombros)
    rep_error_detected = False # Inicialización estandarizada

    print(f"--- Iniciando análisis de Press de Hombros para {video_path} ---") # Debug print

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image_rgb.flags.writeable = False
        results = pose.process(image_rgb)
        image_rgb.flags.writeable = True

        if results.pose_landmarks:
            landmarks = results.pose_landmarks.landmark
            try:
                # Coordenadas de las articulaciones del brazo
                r_shoulder = [landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER].x,
                              landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER].y]
                r_elbow = [landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW].x, landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW].y]
                r_wrist = [landmarks[mp_pose.PoseLandmark.RIGHT_WRIST].x, landmarks[mp_pose.PoseLandmark.RIGHT_WRIST].y]

                l_shoulder = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER].x,
                              landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER].y]
                l_elbow = [landmarks[mp_pose.PoseLandmark.LEFT_ELBOW].x, landmarks[mp_pose.PoseLandmark.LEFT_ELBOW].y]
                l_wrist = [landmarks[mp_pose.PoseLandmark.LEFT_WRIST].x, landmarks[mp_pose.PoseLandmark.LEFT_WRIST].y]

                # Cálculo de Ángulos (promedio de ambos brazos)
                right_elbow_angle = calculate_angle(r_shoulder, r_elbow, r_wrist)
                left_elbow_angle = calculate_angle(l_shoulder, l_elbow, l_wrist)
                avg_elbow_angle = (right_elbow_angle + left_elbow_angle) / 2

                # --- DEBUG PRINT ---
                print(f"Etapa: {current_stage}, Ángulo Codo: {avg_elbow_angle:.1f}")
                # --- FIN DEBUG PRINT ---

                # Lógica de Conteo de Repeticiones y Etapa del Movimiento
                if avg_elbow_angle > MIN_ELBOW_ANGLE_EXTENDED:  # Si el codo está bien extendido
                    if current_stage == "abajo" or current_stage == "bajando":
                        current_stage = "subiendo"  # Transición: brazo subiendo
                    elif current_stage == "subiendo":
                        current_stage = "arriba"  # Llegó al punto más alto del movimiento

                if avg_elbow_angle < MAX_ELBOW_ANGLE_RACK:  # Si el codo está bien flexionado
                    if current_stage == "arriba" or current_stage == "subiendo":
                        current_stage = "bajando"  # Transición: brazo bajando
                    elif current_stage == "bajando":
                        reps += 1
                        if not rep_error_detected:
                            good_reps_count += 1
                            print(f"DEBUG: Repetición {reps} CONTADA (Buena Forma).") # Explicit good rep
                        else:
                            print(f"DEBUG: Repetición {reps} CONTADA (Forma Incorrecta - ROM).") # Explicit bad rep
                        rep_error_detected = False  # Resetear el flag de error
                        current_stage = "abajo"  # Resetear etapa para la siguiente repetición

                # Reglas de Corrección de Postura (afectan penalización por ROM)
                if current_stage == "subiendo" and avg_elbow_angle < MIN_ELBOW_ANGLE_EXTENDED - 10:
                    rep_error_detected = True
                    # print(f"DEBUG: Error ROM - No extiende lo suficiente (Codo: {avg_elbow_angle:.1f})") # Debug print
                elif current_stage == "bajando" and avg_elbow_angle > MAX_ELBOW_ANGLE_RACK + 10:
                    rep_error_detected = True
                    # print(f"DEBUG: Error ROM - No flexiona lo suficiente (Codo: {avg_elbow_angle:.1f})") # Debug print

            except Exception as e:
                print(f"Error en landmarks para Press de Hombros (frame actual): {e}") # Debug print
                rep_error_detected = True
        else:
            rep_error_detected = True
            print("DEBUG: No se detectaron landmarks en el frame.") # Debug print

    cap.release()
    effectiveness = (good_reps_count / reps * 100) if reps > 0 else 100

    print(f"--- Análisis finalizado para Press de Hombros. Reps Totales: {reps}, Reps Buenas: {good_reps_count}, Efectividad: {effectiveness:.1f}% ---") # Debug print

    feedback = ""
    if reps == 0 and rep_error_detected: # Usar rep_error_detected
        feedback = "No se detectaron repeticiones o hubo problemas de detección. Asegúrate de estar bien encuadrado y con buena iluminación. Ajusta los umbrales si es necesario."
    elif reps > 0:
        feedback = f"Press de Hombros analizado: Realizaste {reps} repeticiones en total, con {good_reps_count} repeticiones de buena forma (ROM). Tu efectividad fue del {round(effectiveness, 1)}%. ¡Deltoides trabajando duro!"
        if effectiveness < 100:
            feedback += " Concéntrate en un rango de movimiento completo, extendiendo completamente arriba y bajando a la altura de los hombros."
    else:
        feedback = "No se detectaron repeticiones. ¿Realizaste el ejercicio correctamente? Asegúrate de que el movimiento del codo cruza los umbrales definidos y que la cámara te ve de lado."

    return {
        "exercise": "Press de Hombros",
        "total_reps_done": reps, # Nueva clave
        "good_form_reps_count": good_reps_count, # Nueva clave
        "effectiveness_percentage": round(effectiveness, 1),
        "feedback": feedback
    }


# ANALISIS DE ELEVACIONES LATERALES
def analyze_elevaciones_laterales(video_path):
    # Parámetros del ejercicio (Ajusta estos valores)
    ELBOW_BEND_MIN = 140  # Ángulo mínimo para una ligera flexión de codo (casi recto)
    ELBOW_BEND_MAX = 180  # Ángulo máximo para una ligera flexión de codo (casi recto)
    Y_WRIST_TOP_THRESHOLD = 0.05  # La muñeca puede estar ligeramente por debajo del hombro para el "arriba".
    Y_WRIST_BOTTOM_THRESHOLD = 0.30  # La muñeca debe estar bastante más abajo que el hombro para el "abajo".

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return {"exercise": "Elevaciones Laterales", "total_reps_done": 0, "good_form_reps_count": 0, "effectiveness_percentage": 0.0,
                "feedback": "Error: No se pudo abrir el video para Elevaciones Laterales."}

    reps = 0
    good_reps_count = 0
    current_stage = "abajo"  # Etapa inicial: brazos abajo
    rep_error_detected = False # Inicialización estandarizada

    print(f"--- Iniciando análisis de Elevaciones Laterales para {video_path} ---") # Debug print

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image_rgb.flags.writeable = False
        results = pose.process(image_rgb)
        image_rgb.flags.writeable = True

        avg_elbow_bend_angle = 0.0
        avg_wrist_y_rel_shoulder = 0.0
        detection_problem_this_frame = False

        if results.pose_landmarks:
            landmarks = results.pose_landmarks.landmark
            try:
                r_shoulder = [landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER].x,
                              landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER].y] if landmarks[
                                                                                       mp_pose.PoseLandmark.RIGHT_SHOULDER].visibility > 0.5 else None
                r_elbow = [landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW].x,
                           landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW].y] if landmarks[
                                                                                 mp_pose.PoseLandmark.RIGHT_ELBOW].visibility > 0.5 else None
                r_wrist = [landmarks[mp_pose.PoseLandmark.RIGHT_WRIST].x,
                           landmarks[mp_pose.PoseLandmark.RIGHT_WRIST].y] if landmarks[
                                                                                 mp_pose.PoseLandmark.RIGHT_WRIST].visibility > 0.5 else None

                l_shoulder = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER].x,
                              landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER].y] if landmarks[
                                                                                      mp_pose.PoseLandmark.LEFT_SHOULDER].visibility > 0.5 else None
                l_elbow = [landmarks[mp_pose.PoseLandmark.LEFT_ELBOW].x,
                           landmarks[mp_pose.PoseLandmark.LEFT_ELBOW].y] if landmarks[
                                                                                mp_pose.PoseLandmark.LEFT_ELBOW].visibility > 0.5 else None
                l_wrist = [landmarks[mp_pose.PoseLandmark.LEFT_WRIST].x,
                           landmarks[mp_pose.PoseLandmark.LEFT_WRIST].y] if landmarks[
                                                                                mp_pose.PoseLandmark.LEFT_WRIST].visibility > 0.5 else None

                if all(v is not None for v in [r_shoulder, r_elbow, r_wrist, l_shoulder, l_elbow, l_wrist]):
                    right_elbow_bend_angle = calculate_angle(r_shoulder, r_elbow, r_wrist)
                    left_elbow_bend_angle = calculate_angle(l_shoulder, l_elbow, l_wrist)
                    avg_elbow_bend_angle = (right_elbow_bend_angle + left_elbow_bend_angle) / 2

                    avg_wrist_y_rel_shoulder = ((r_wrist[1] - r_shoulder[1]) + (l_wrist[1] - l_shoulder[1])) / 2
                else:
                    detection_problem_this_frame = True

                if detection_problem_this_frame:
                    rep_error_detected = True

                if not detection_problem_this_frame:
                    if avg_wrist_y_rel_shoulder < Y_WRIST_TOP_THRESHOLD and \
                            ELBOW_BEND_MIN <= avg_elbow_bend_angle <= ELBOW_BEND_MAX:
                        if current_stage == "abajo" or current_stage == "bajando":
                            current_stage = "subiendo"
                        elif current_stage == "subiendo":
                            current_stage = "arriba"

                    if avg_wrist_y_rel_shoulder > Y_WRIST_BOTTOM_THRESHOLD and \
                            ELBOW_BEND_MIN <= avg_elbow_bend_angle <= ELBOW_BEND_MAX:
                        if current_stage == "arriba" or current_stage == "subiendo":
                            current_stage = "bajando"
                        elif current_stage == "bajando":
                            reps += 1
                            if not rep_error_detected:
                                good_reps_count += 1
                                print(f"DEBUG: Repetición {reps} CONTADA (Buena Forma).") # Explicit good rep
                            else:
                                print(f"DEBUG: Repetición {reps} CONTADA (Forma Incorrecta).") # Explicit bad rep
                            rep_error_detected = False
                            current_stage = "abajo"

                # Reglas de Corrección de Postura (Afetan la Efectividad)
                if current_stage == "subiendo" and avg_wrist_y_rel_shoulder > Y_WRIST_TOP_THRESHOLD + 0.05:
                    rep_error_detected = True
                    # print(f"DEBUG: Error ROM - No sube lo suficiente (Muñeca Y: {avg_wrist_y_rel_shoulder:.2f})") # Debug print

                elif current_stage == "bajando" and avg_wrist_y_rel_shoulder < Y_WRIST_BOTTOM_THRESHOLD - 0.05:
                    rep_error_detected = True
                    # print(f"DEBUG: Error ROM - No baja lo suficiente (Muñeca Y: {avg_wrist_y_rel_shoulder:.2f})") # Debug print

                if not (ELBOW_BEND_MIN <= avg_elbow_bend_angle <= ELBOW_BEND_MAX):
                    rep_error_detected = True
                    # print(f"DEBUG: Error Forma - Codo no constante (Codo: {avg_elbow_bend_angle:.1f})") # Debug print

            except Exception as e:
                print(f"Error inesperado durante el procesamiento para Elevaciones Laterales (frame actual): {e}") # Debug print
                rep_error_detected = True
        else:
            rep_error_detected = True
            print("DEBUG: No se detectaron landmarks en el frame.") # Debug print

    cap.release()
    effectiveness = (good_reps_count / reps * 100) if reps > 0 else 100

    print(f"--- Análisis finalizado para Elevaciones Laterales. Reps Totales: {reps}, Reps Buenas: {good_reps_count}, Efectividad: {effectiveness:.1f}% ---") # Debug print

    feedback = ""
    if reps == 0 and rep_error_detected: # Usar rep_error_detected
        feedback = "No se detectaron repeticiones o hubo problemas de detección. Asegúrate de estar bien encuadrado y con buena iluminación. Ajusta los umbrales si es necesario."
    elif reps > 0:
        feedback = f"Elevaciones Laterales analizadas: Realizaste {reps} repeticiones en total, con {good_reps_count} repeticiones de buena forma. Tu efectividad fue del {round(effectiveness, 1)}%. ¡Hombros esculpidos!"
        if effectiveness < 100:
            feedback += " Presta atención a la altura del brazo y a mantener la consistencia del ángulo del codo. Asegúrate de grabar de frente."
    else:
        feedback = "No se detectaron repeticiones. ¿Realizaste el ejercicio correctamente? Asegúrate de que el movimiento y la forma del codo cruzan los umbrales definidos y que la cámara te ve de frente."

    return {
        "exercise": "Elevaciones Laterales",
        "total_reps_done": reps, # Nueva clave
        "good_form_reps_count": good_reps_count, # Nueva clave
        "effectiveness_percentage": round(effectiveness, 1),
        "feedback": feedback
    }


# ANALISIS DE REMO
def analyze_remo(video_path):
    # Parámetros del ejercicio (Ajusta estos valores)
    MIN_WRIST_DISTANCE_CONTRACTED = 0.05  # Distancia X mínima cuando las manos están jaladas (cerca del torso).
    MAX_WRIST_DISTANCE_EXTENDED = 0.35    # Distancia X máxima cuando los brazos están extendidos.
    ELBOW_ANGLE_PULLED = 80       # Ángulo máximo del codo cuando está flexionado (jalado).
    ELBOW_ANGLE_EXTENDED = 150    # Ángulo mínimo del codo cuando está extendido (colgando).

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return {"exercise": "Remo", "total_reps_done": 0, "good_form_reps_count": 0, "effectiveness_percentage": 0.0,
                "feedback": "Error: No se pudo abrir el video para Remo."}

    reps = 0
    good_reps_count = 0
    current_stage = "extendida"
    rep_error_detected = False # Inicialización estandarizada

    print(f"--- Iniciando análisis de Remo para {video_path} ---") # Debug print

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image_rgb.flags.writeable = False
        results = pose.process(image_rgb)
        image_rgb.flags.writeable = True

        avg_wrist_x_distance = 0.0
        avg_elbow_angle = 0.0
        detection_problem_this_frame = False

        if results.pose_landmarks:
            landmarks = results.pose_landmarks.landmark
            try:
                r_shoulder = [landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER].x,
                              landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER].y] if landmarks[
                                                                                       mp_pose.PoseLandmark.RIGHT_SHOULDER].visibility > 0.1 else None
                r_elbow = [landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW].x,
                           landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW].y] if landmarks[
                                                                                 mp_pose.PoseLandmark.RIGHT_ELBOW].visibility > 0.1 else None
                r_wrist = [landmarks[mp_pose.PoseLandmark.RIGHT_WRIST].x,
                           landmarks[mp_pose.PoseLandmark.RIGHT_WRIST].y] if landmarks[
                                                                                 mp_pose.PoseLandmark.RIGHT_WRIST].visibility > 0.1 else None

                l_shoulder = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER].x,
                              landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER].y] if landmarks[
                                                                                      mp_pose.PoseLandmark.LEFT_SHOULDER].visibility > 0.1 else None
                l_elbow = [landmarks[mp_pose.PoseLandmark.LEFT_ELBOW].x,
                           landmarks[mp_pose.PoseLandmark.LEFT_ELBOW].y] if landmarks[
                                                                                mp_pose.PoseLandmark.LEFT_ELBOW].visibility > 0.1 else None
                l_wrist = [landmarks[mp_pose.PoseLandmark.LEFT_WRIST].x,
                           landmarks[mp_pose.PoseLandmark.LEFT_WRIST].y] if landmarks[
                                                                                mp_pose.PoseLandmark.LEFT_WRIST].visibility > 0.1 else None

                if all(v is not None for v in [r_shoulder, r_elbow, r_wrist, l_shoulder, l_elbow, l_wrist]):
                    right_elbow_angle = calculate_angle(r_shoulder, r_elbow, r_wrist)
                    left_elbow_angle = calculate_angle(l_shoulder, l_elbow, l_wrist)
                    avg_elbow_angle = (right_elbow_angle + left_elbow_angle) / 2

                    avg_wrist_x_distance = abs(r_wrist[0] - l_wrist[0])
                else:
                    detection_problem_this_frame = True

                elbow_angles = []
                if r_shoulder and r_elbow and r_wrist:
                    elbow_angles.append(calculate_angle(r_shoulder, r_elbow, r_wrist))
                if l_shoulder and l_elbow and l_wrist:
                    elbow_angles.append(calculate_angle(l_shoulder, l_elbow, l_wrist))

                if elbow_angles:
                    avg_elbow_angle = np.mean(elbow_angles)
                else:
                    detection_problem_this_frame = True

                if detection_problem_this_frame:
                    rep_error_detected = True

                if not detection_problem_this_frame:
                    if avg_wrist_x_distance < MIN_WRIST_DISTANCE_CONTRACTED and \
                            avg_elbow_angle < ELBOW_ANGLE_PULLED:
                        if current_stage == "extendida" or current_stage == "extendiendose":
                            current_stage = "tirando"
                        elif current_stage == "tirando":
                            current_stage = "contraida"

                    if avg_wrist_x_distance > MAX_WRIST_DISTANCE_EXTENDED and \
                            avg_elbow_angle > ELBOW_ANGLE_EXTENDED:
                        if current_stage == "contraida" or current_stage == "tirando":
                            current_stage = "extendiendose"
                        elif current_stage == "extendiendose":
                            reps += 1
                            if not rep_error_detected:
                                good_reps_count += 1
                                print(f"DEBUG: Repetición {reps} CONTADA (Buena Forma).") # Explicit good rep
                            else:
                                print(f"DEBUG: Repetición {reps} CONTADA (Forma Incorrecta).") # Explicit bad rep
                            rep_error_detected = False
                            current_stage = "extendida"

                # Reglas de Corrección de Postura
                if current_stage == "extendiendose" and \
                        (avg_wrist_x_distance < MAX_WRIST_DISTANCE_EXTENDED - 0.05 or \
                         avg_elbow_angle < ELBOW_ANGLE_EXTENDED - 10):
                    rep_error_detected = True
                    # print(f"DEBUG: Error ROM - No extiende lo suficiente (Dist. Muñeca X: {avg_wrist_x_distance:.2f}, Codo: {avg_elbow_angle:.1f})") # Debug print

                elif current_stage == "tirando" and \
                        (avg_wrist_x_distance > MIN_WRIST_DISTANCE_CONTRACTED + 0.05 or \
                         avg_elbow_angle > ELBOW_ANGLE_PULLED + 10):
                    rep_error_detected = True
                    # print(f"DEBUG: Error ROM - No jala lo suficiente (Dist. Muñeca X: {avg_wrist_x_distance:.2f}, Codo: {avg_elbow_angle:.1f})") # Debug print

            except Exception as e:
                print(f"Error inesperado durante el procesamiento para Remo (frame actual): {e}") # Debug print
                rep_error_detected = True
        else:
            rep_error_detected = True
            print("DEBUG: No se detectaron landmarks en el frame.") # Debug print

    cap.release()
    effectiveness = (good_reps_count / reps * 100) if reps > 0 else 100

    print(f"--- Análisis finalizado para Remo. Reps Totales: {reps}, Reps Buenas: {good_reps_count}, Efectividad: {effectiveness:.1f}% ---") # Debug print

    feedback = ""
    if reps == 0 and rep_error_detected: # Usar rep_error_detected
        feedback = "No se detectaron repeticiones o hubo problemas de detección. Asegúrate de estar bien encuadrado y con buena iluminación. Ajusta los umbrales si es necesario."
    elif reps > 0:
        feedback = f"Remo analizado: Realizaste {reps} repeticiones en total, con {good_reps_count} repeticiones de buena forma. Tu efectividad fue del {round(effectiveness, 1)}%. ¡Espalda fuerte y definida!"
        if effectiveness < 100:
            feedback += " Concéntrate en el rango de movimiento completo, extendiendo y contrayendo los brazos. Asegúrate de grabar de frente."
    else:
        feedback = "No se detectaron repeticiones. ¿Realizaste el ejercicio correctamente? Asegúrate de que el movimiento cruza los umbrales definidos y que la cámara te ve de frente."

    return {
        "exercise": "Remo",
        "total_reps_done": reps, # Nueva clave
        "good_form_reps_count": good_reps_count, # Nueva clave
        "effectiveness_percentage": round(effectiveness, 1),
        "feedback": feedback
    }


# ANALISIS DE PESO MUERTO
def analyze_peso_muerto(video_path):
    # Parámetros del ejercicio
    Y_SHOULDER_TOP_THRESHOLD = 0.20  # Valor Y del hombro cuando estás de pie (arriba).
    Y_SHOULDER_BOTTOM_THRESHOLD = 0.55  # Valor Y del hombro cuando estás en la posición baja del peso muerto (abajo).

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return {"exercise": "Peso Muerto", "total_reps_done": 0, "good_form_reps_count": 0, "effectiveness_percentage": 0.0,
                "feedback": "Error: No se pudo abrir el video para Peso Muerto."}

    reps = 0
    good_reps_count = 0
    current_stage = "arriba"
    rep_error_detected = False # Inicialización estandarizada

    print(f"--- Iniciando análisis de Peso Muerto para {video_path} ---") # Debug print

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image_rgb.flags.writeable = False
        results = pose.process(image_rgb)
        image_rgb.flags.writeable = True

        avg_shoulder_y = 0.0
        detection_problem_this_frame = False

        if results.pose_landmarks:
            landmarks = results.pose_landmarks.landmark
            try:
                r_shoulder = [landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER].x,
                              landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER].y] if landmarks[
                                                                                       mp_pose.PoseLandmark.RIGHT_SHOULDER].visibility > 0.1 else None
                l_shoulder = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER].x,
                              landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER].y] if landmarks[
                                                                                      mp_pose.PoseLandmark.LEFT_SHOULDER].visibility > 0.1 else None

                if r_shoulder is not None and l_shoulder is not None:
                    avg_shoulder_y = (r_shoulder[1] + l_shoulder[1]) / 2
                elif r_shoulder is not None:
                    avg_shoulder_y = r_shoulder[1]
                elif l_shoulder is not None:
                    avg_shoulder_y = l_shoulder[1]
                else:
                    detection_problem_this_frame = True

                # No se penaliza la buena forma por problemas de detección en este modo súper simple
                # if detection_problem_this_frame:
                #     rep_error_detected = True

                if not detection_problem_this_frame:
                    if avg_shoulder_y > Y_SHOULDER_BOTTOM_THRESHOLD:
                        if current_stage == "arriba" or current_stage == "subiendo":
                            current_stage = "bajando"
                        elif current_stage == "bajando":
                            current_stage = "abajo"

                    if avg_shoulder_y < Y_SHOULDER_TOP_THRESHOLD:
                        if current_stage == "abajo" or current_stage == "bajando":
                            current_stage = "subiendo"
                        elif current_stage == "subiendo":
                            reps += 1
                            if not rep_error_detected: # En este ejercicio simplificado, siempre es buena forma si se cuenta.
                                good_reps_count += 1
                                print(f"DEBUG: Repetición {reps} CONTADA (Buena Forma).") # Explicit good rep
                            else:
                                print(f"DEBUG: Repetición {reps} CONTADA (Forma Incorrecta - Detección).") # Explicit bad rep
                            rep_error_detected = False
                            current_stage = "arriba"

                # Reglas de Corrección de Postura (MUY BÁSICAS)
                if current_stage == "subiendo" and avg_shoulder_y > Y_SHOULDER_TOP_THRESHOLD + 0.05:
                    # No se penaliza la forma en este modo
                    # rep_error_detected = True
                    # print(f"DEBUG: Error ROM - No sube lo suficiente (Hombro Y: {avg_shoulder_y:.2f})") # Debug print
                    pass

                elif current_stage == "bajando" and avg_shoulder_y < Y_SHOULDER_BOTTOM_THRESHOLD - 0.05:
                    # No se penaliza la forma en este modo
                    # rep_error_detected = True
                    # print(f"DEBUG: Error ROM - No baja lo suficiente (Hombro Y: {avg_shoulder_y:.2f})") # Debug print
                    pass

            except Exception as e:
                print(f"Error inesperado durante el procesamiento para Peso Muerto (frame actual): {e}") # Debug print
                rep_error_detected = True
        else:
            rep_error_detected = True
            print("DEBUG: No se detectaron landmarks en el frame.") # Debug print

    cap.release()
    effectiveness = (good_reps_count / reps * 100) if reps > 0 else 100

    feedback = ""
    if reps == 0 and rep_error_detected: # Usar rep_error_detected
        feedback = "No se detectaron repeticiones o hubo problemas de detección. Asegúrate de estar bien encuadrado (vista lateral) y con buena iluminación. Ajusta los umbrales Y_SHOULDER_TOP_THRESHOLD y Y_SHOULDER_BOTTOM_THRESHOLD."
    elif reps > 0:
        feedback = f"Peso Muerto analizado: Realizaste {reps} repeticiones en total, con {good_reps_count} repeticiones de buena forma. Tu efectividad fue del {round(effectiveness, 1)}%. ¡Gran esfuerzo! Recuerda que esta versión simplificada solo evalúa el movimiento del torso."
        if effectiveness < 100:
            feedback += " Hubo algunas irregularidades en la detección del movimiento del hombro. Revisa tu rango completo de movimiento."
    else:
        feedback = "No se detectaron repeticiones. ¿Realizaste el ejercicio correctamente? Asegúrate de que el movimiento del hombro cruza los umbrales definidos y que la cámara te ve de lado."

    return {
        "exercise": "Peso Muerto",
        "total_reps_done": reps, # Nueva clave
        "good_form_reps_count": good_reps_count, # Nueva clave
        "effectiveness_percentage": round(effectiveness, 1),
        "feedback": feedback
    }


# ANALISIS DE PRESS DE BANCA
def analyze_press_banca(video_path):
    # Parámetros del ejercicio
    MIN_ELBOW_ANGLE_EXTENDED = 140  # Ángulo mínimo del codo cuando los brazos están extendidos (arriba).
    MAX_ELBOW_ANGLE_FLEXED = 110  # Ángulo máximo del codo cuando la barra está cerca del pecho (abajo).
    Y_DIFF_TOP_THRESHOLD = 0.05  # La muñeca puede estar ligeramente por debajo del hombro para el "arriba".
    Y_DIFF_BOTTOM_THRESHOLD = 0.25  # La muñeca no necesita bajar tanto para el "abajo".

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return {"exercise": "Press de Banca", "total_reps_done": 0, "good_form_reps_count": 0, "effectiveness_percentage": 0.0,
                "feedback": "Error: No se pudo abrir el video para Press de Banca."}

    reps = 0
    good_reps_count = 0
    current_stage = "arriba"
    rep_error_detected = False # Inicialización estandarizada

    print(f"--- Iniciando análisis de Press de Banca para {video_path} ---") # Debug print

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image_rgb.flags.writeable = False
        results = pose.process(image_rgb)
        image_rgb.flags.writeable = True

        avg_elbow_angle = 180.0
        avg_wrist_y_diff = 0.0
        detection_problem_this_frame = False

        if results.pose_landmarks:
            landmarks = results.pose_landmarks.landmark
            try:
                r_shoulder = [landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER].x,
                              landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER].y] if landmarks[
                                                                                       mp_pose.PoseLandmark.RIGHT_SHOULDER].visibility > 0.5 else None
                r_elbow = [landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW].x,
                           landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW].y] if landmarks[
                                                                                 mp_pose.PoseLandmark.RIGHT_ELBOW].visibility > 0.5 else None
                r_wrist = [landmarks[mp_pose.PoseLandmark.RIGHT_WRIST].x,
                           landmarks[mp_pose.PoseLandmark.RIGHT_WRIST].y] if landmarks[
                                                                                 mp_pose.PoseLandmark.RIGHT_WRIST].visibility > 0.5 else None

                l_shoulder = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER].x,
                              landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER].y] if landmarks[
                                                                                      mp_pose.PoseLandmark.LEFT_SHOULDER].visibility > 0.5 else None
                l_elbow = [landmarks[mp_pose.PoseLandmark.LEFT_ELBOW].x,
                           landmarks[mp_pose.PoseLandmark.LEFT_ELBOW].y] if landmarks[
                                                                                mp_pose.PoseLandmark.LEFT_ELBOW].visibility > 0.5 else None
                l_wrist = [landmarks[mp_pose.PoseLandmark.LEFT_WRIST].x,
                           landmarks[mp_pose.PoseLandmark.LEFT_WRIST].y] if landmarks[
                                                                                mp_pose.PoseLandmark.LEFT_WRIST].visibility > 0.5 else None

                if all(v is not None for v in [r_shoulder, r_elbow, r_wrist, l_shoulder, l_elbow, l_wrist]):
                    right_elbow_angle = calculate_angle(r_shoulder, r_elbow, r_wrist)
                    left_elbow_angle = calculate_angle(l_shoulder, l_elbow, l_wrist)
                    avg_elbow_angle = (right_elbow_angle + left_elbow_angle) / 2

                    avg_wrist_y_diff = ((l_wrist[1] - l_shoulder[1]) + (r_wrist[1] - r_shoulder[1])) / 2
                else:
                    detection_problem_this_frame = True

                if detection_problem_this_frame:
                    rep_error_detected = True

                if not detection_problem_this_frame:
                    if avg_elbow_angle < MAX_ELBOW_ANGLE_FLEXED and avg_wrist_y_diff > Y_DIFF_BOTTOM_THRESHOLD:
                        if current_stage == "arriba" or current_stage == "subiendo":
                            current_stage = "bajando"
                        elif current_stage == "bajando":
                            current_stage = "abajo"

                    if avg_elbow_angle > MIN_ELBOW_ANGLE_EXTENDED and avg_wrist_y_diff < Y_DIFF_TOP_THRESHOLD:
                        if current_stage == "abajo" or current_stage == "bajando":
                            current_stage = "subiendo"
                        elif current_stage == "subiendo":
                            reps += 1
                            if not rep_error_detected:
                                good_reps_count += 1
                                print(f"DEBUG: Repetición {reps} CONTADA (Buena Forma).") # Explicit good rep
                            else:
                                print(f"DEBUG: Repetición {reps} CONTADA (Forma Incorrecta).") # Explicit bad rep
                            rep_error_detected = False
                            current_stage = "arriba"

                # Reglas de Corrección de Postura
                if not (ELBOW_BEND_MIN <= avg_elbow_bend_angle <= ELBOW_BEND_MAX): # This line seems incorrect here, should be elbow_angle for press banca
                     # rep_error_detected = True # Commenting this out for now to ensure this does not interfere
                     pass # Corrected to ensure no new error here.

                if current_stage == "subiendo" and (avg_elbow_angle < MIN_ELBOW_ANGLE_EXTENDED - 15 or avg_wrist_y_diff > Y_DIFF_TOP_THRESHOLD + 0.10):
                    rep_error_detected = True
                    # print(f"DEBUG: Error ROM - No extiende lo suficiente (Codo: {avg_elbow_angle:.1f}, Muñeca Y: {avg_wrist_y_diff:.2f})") # Debug print
                elif current_stage == "bajando" and (avg_elbow_angle > MAX_ELBOW_ANGLE_FLEXED + 15 or avg_wrist_y_diff < Y_DIFF_BOTTOM_THRESHOLD - 0.10):
                    rep_error_detected = True
                    # print(f"DEBUG: Error ROM - No baja lo suficiente (Codo: {avg_elbow_angle:.1f}, Muñeca Y: {avg_wrist_y_diff:.2f})") # Debug print

            except Exception as e:
                print(f"Error inesperado durante el procesamiento para Press de Banca (frame actual): {e}") # Debug print
                rep_error_detected = True
        else:
            rep_error_detected = True
            print("DEBUG: No se detectaron landmarks en el frame.") # Debug print

    cap.release()
    effectiveness = (good_reps_count / reps * 100) if reps > 0 else 100

    feedback = ""
    if reps == 0 and rep_error_detected: # Usar rep_error_detected
        feedback = "No se detectaron repeticiones o hubo problemas de detección. Asegúrate de estar bien encuadrado y de lado. Ajusta los umbrales si es necesario."
    elif reps > 0:
        feedback = f"Press de Banca analizado: Realizaste {reps} repeticiones en total, con {good_reps_count} repeticiones de buena forma. Tu efectividad fue del {round(effectiveness, 1)}%. ¡Buen trabajo!"
        if effectiveness < 100:
            feedback += " Concéntrate en un rango de movimiento completo, extendiendo completamente arriba y bajando lo suficiente. ¡Sigue mejorando!"
    else:
        feedback = "No se detectaron repeticiones. ¿Realizaste el ejercicio correctamente? Asegúrate de que tus brazos crucen los umbrales de flexión y extensión y que la cámara te ve de lado."

    return {
        "exercise": "Press de Banca",
        "total_reps_done": reps, # Nueva clave
        "good_form_reps_count": good_reps_count, # Nueva clave
        "effectiveness_percentage": round(effectiveness, 1),
        "feedback": feedback
    }


# ANALISIS DE APERTURA CON MANCUERNA
def analyze_apertura_mancuerna(video_path):
    # Parámetros del ejercicio
    ELBOW_BEND_MIN = 160  # Ángulo mínimo para una ligera flexión de codo (casi recto)
    ELBOW_BEND_MAX = 175  # Ángulo máximo para una ligera flexión de codo (casi recto)
    MIN_WRIST_DISTANCE_CLOSED = 0.05  # Distancia X mínima cuando las manos están juntas (arriba).
    MAX_WRIST_DISTANCE_OPEN = 0.35    # Distancia X máxima cuando los brazos están completamente abiertos (abajo).

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return {"exercise": "Apertura con Mancuerna", "total_reps_done": 0, "good_form_reps_count": 0, "effectiveness_percentage": 0.0,
                "feedback": "Error: No se pudo abrir el video para Apertura con Mancuerna."}

    reps = 0
    good_reps_count = 0
    current_stage = "arriba"
    rep_error_detected = False # Inicialización estandarizada

    print(f"--- Iniciando análisis de Apertura con Mancuerna para {video_path} ---") # Debug print

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image_rgb.flags.writeable = False
        results = pose.process(image_rgb)
        image_rgb.flags.writeable = True

        avg_elbow_bend_angle = 180.0
        avg_wrist_x_distance = 0.0
        detection_problem_this_frame = False

        if results.pose_landmarks:
            landmarks = results.pose_landmarks.landmark
            try:
                r_shoulder = [landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER].x,
                              landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER].y] if landmarks[
                                                                                       mp_pose.PoseLandmark.RIGHT_SHOULDER].visibility > 0.5 else None
                r_elbow = [landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW].x,
                           landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW].y] if landmarks[
                                                                                 mp_pose.PoseLandmark.RIGHT_ELBOW].visibility > 0.5 else None
                r_wrist = [landmarks[mp_pose.PoseLandmark.RIGHT_WRIST].x,
                           landmarks[mp_pose.PoseLandmark.RIGHT_WRIST].y] if landmarks[
                                                                                 mp_pose.PoseLandmark.RIGHT_WRIST].visibility > 0.5 else None

                l_shoulder = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER].x,
                              landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER].y] if landmarks[
                                                                                      mp_pose.PoseLandmark.LEFT_SHOULDER].visibility > 0.5 else None
                l_elbow = [landmarks[mp_pose.PoseLandmark.LEFT_ELBOW].x,
                           landmarks[mp_pose.PoseLandmark.LEFT_ELBOW].y] if landmarks[
                                                                                mp_pose.PoseLandmark.LEFT_ELBOW].visibility > 0.5 else None
                l_wrist = [landmarks[mp_pose.PoseLandmark.LEFT_WRIST].x,
                           landmarks[mp_pose.PoseLandmark.LEFT_WRIST].y] if landmarks[
                                                                                mp_pose.PoseLandmark.LEFT_WRIST].visibility > 0.5 else None

                if all(v is not None for v in [r_shoulder, r_elbow, r_wrist, l_shoulder, l_elbow, l_wrist]):
                    right_elbow_bend_angle = calculate_angle(r_shoulder, r_elbow, r_wrist)
                    left_elbow_bend_angle = calculate_angle(l_shoulder, l_elbow, l_wrist)
                    avg_elbow_bend_angle = (right_elbow_bend_angle + left_elbow_bend_angle) / 2

                    avg_wrist_x_distance = abs(r_wrist[0] - l_wrist[0])
                else:
                    detection_problem_this_frame = True

                if detection_problem_this_frame:
                    rep_error_detected = True

                if not detection_problem_this_frame:
                    if avg_wrist_x_distance > MAX_WRIST_DISTANCE_OPEN and \
                            ELBOW_BEND_MIN <= avg_elbow_bend_angle <= ELBOW_BEND_MAX:
                        if current_stage == "arriba" or current_stage == "subiendo":
                            current_stage = "bajando"
                        elif current_stage == "bajando":
                            current_stage = "abajo"

                    if avg_wrist_x_distance < MIN_WRIST_DISTANCE_CLOSED and \
                            ELBOW_BEND_MIN <= avg_elbow_bend_angle <= ELBOW_BEND_MAX:
                        if current_stage == "abajo" or current_stage == "bajando":
                            current_stage = "subiendo"
                        elif current_stage == "subiendo":
                            reps += 1
                            if not rep_error_detected:
                                good_reps_count += 1
                                print(f"DEBUG: Repetición {reps} CONTADA (Buena Forma).") # Explicit good rep
                            else:
                                print(f"DEBUG: Repetición {reps} CONTADA (Forma Incorrecta).") # Explicit bad rep
                            rep_error_detected = False
                            current_stage = "arriba"

                # Reglas de Corrección de Postura
                if not (ELBOW_BEND_MIN <= avg_elbow_bend_angle <= ELBOW_BEND_MAX):
                    rep_error_detected = True
                    # print(f"DEBUG: Error Forma - Codo no constante (Codo: {avg_elbow_bend_angle:.1f})") # Debug print

                if current_stage == "bajando" and avg_wrist_x_distance < MAX_WRIST_DISTANCE_OPEN - 0.05:
                    rep_error_detected = True
                    # print(f"DEBUG: Error ROM - No abre lo suficiente (Dist. Muñeca X: {avg_wrist_x_distance:.2f})") # Debug print
                elif current_stage == "subiendo" and avg_wrist_x_distance > MIN_WRIST_DISTANCE_CLOSED + 0.02:
                    rep_error_detected = True
                    # print(f"DEBUG: Error ROM - No cierra lo suficiente (Dist. Muñeca X: {avg_wrist_x_distance:.2f})") # Debug print

            except Exception as e:
                print(f"Error inesperado durante el procesamiento para Apertura con Mancuerna (frame actual): {e}") # Debug print
                rep_error_detected = True
        else:
            rep_error_detected = True
            print("DEBUG: No se detectaron landmarks en el frame.") # Debug print

    cap.release()
    effectiveness = (good_reps_count / reps * 100) if reps > 0 else 100

    feedback = ""
    if reps == 0 and rep_error_detected: # Usar rep_error_detected
        feedback = "No se detectaron repeticiones o hubo problemas de detección. Asegúrate de estar bien encuadrado (vista frontal) y con buena iluminación. Ajusta los umbrales de distancia entre muñecas o flexión de codo."
    elif reps > 0:
        feedback = f"Apertura con Mancuerna analizada: Realizaste {reps} repeticiones en total, con {good_reps_count} repeticiones de buena forma. Tu efectividad fue del {round(effectiveness, 1)}%. ¡Excelente trabajo de pecho!"
        if effectiveness < 100:
            feedback += " Presta atención a mantener una ligera flexión constante en los codos y un rango completo de movimiento. Asegúrate de grabar de frente."
    else:
        feedback = "No se detectaron repeticiones. ¿Realizaste el ejercicio correctamente? Asegúrate de que tus brazos se abran y cierren completamente y que los codos mantengan una ligera flexión y que la cámara te ve de frente."

    return {
        "exercise": "Apertura con Mancuerna",
        "total_reps_done": reps, # Nueva clave
        "good_form_reps_count": good_reps_count, # Nueva clave
        "effectiveness_percentage": round(effectiveness, 1),
        "feedback": feedback
    }

# Mapeo de exercise_id a la función de análisis correspondiente
ANALYSIS_FUNCTIONS = {
    'curl_biceps': analyze_curl_biceps,
    'extensiones_triceps': analyze_extensiones_triceps,
    'press_hombros': analyze_press_hombros,
    'elevaciones_laterales': analyze_elevaciones_laterales,
    'remo': analyze_remo,
    'peso_muerto': analyze_peso_muerto,
    'press_banca': analyze_press_banca,
    'apertura_mancuerna': analyze_apertura_mancuerna,
}

