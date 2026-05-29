import cv2
import pytesseract
import re
import sys
from database import verificar_placa, salvar_historico

sys.stdout.reconfigure(line_buffering=True)

pytesseract.pytesseract.tesseract_cmd = r"C:\Users\49182867801\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"

placa_ja_registrada = None

def extrair_placa(texto):
    texto = texto.upper()
    texto = re.sub(r'[^A-Z0-9]', '', texto)

    texto = texto.replace('O', '0')
    texto = texto.replace('I', '1')
    texto = texto.replace('Z', '2')
    texto = texto.replace('S', '5')

    match = re.search(r'[A-Z]{3}[0-9][A-Z0-9][0-9]{2}', texto)
    if match:
        return match.group()

    match2 = re.search(r'[A-Z]{3}[0-9]{4}', texto)
    if match2:
        return match2.group()

    return None


def preprocessar(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.bilateralFilter(gray, 11, 17, 17)

    thresh = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_MEAN_C,
        cv2.THRESH_BINARY_INV,
        19, 9
    )

    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    morph = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

    return morph


def gerar_frames():
    global placa_ja_registrada

    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

    placa_status = ""

    while True:
        sucesso, frame = cap.read()
        if not sucesso:
            break

        display = frame.copy()
        processada = preprocessar(frame)

        contornos, _ = cv2.findContours(
            processada, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        contornos = sorted(contornos, key=cv2.contourArea, reverse=True)[:15]

        for contorno in contornos:
            area = cv2.contourArea(contorno)
            if area < 4000:
                continue

            x, y, w, h = cv2.boundingRect(contorno)
            proporcao = w / float(h)

            if 2.2 < proporcao < 5.5:
                placa_img = frame[y:y+h, x:x+w]
                placa_proc = preprocessar(placa_img)

                config = r'--oem 3 --psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
                texto = pytesseract.image_to_string(placa_proc, config=config)

                placa = extrair_placa(texto)

                if placa:

                    if placa != placa_ja_registrada:

                        veiculo = verificar_placa(placa)

                        if veiculo:
                            placa_status = "ENTRADA AUTORIZADA"
                            cor = (0, 255, 0)

                        else:
                            placa_status = "VEICULO NAO ENCONTRADO"
                            cor = (0, 0, 255)

                        salvar_historico(placa, placa_status)

                        placa_ja_registrada = placa

                    # QUADRADO DETECTOR
                    cv2.rectangle(
                        display,
                        (x, y),
                        (x + w, y + h),
                        cor,
                        4
                    )

                    # CANTOS FUTURISTAS
                    tamanho = 25

                    # canto superior esquerdo
                    cv2.line(display, (x, y), (x + tamanho, y), cor, 4)
                    cv2.line(display, (x, y), (x, y + tamanho), cor, 4)

                    # superior direito
                    cv2.line(display, (x + w, y), (x + w - tamanho, y), cor, 4)
                    cv2.line(display, (x + w, y), (x + w, y + tamanho), cor, 4)

                    # inferior esquerdo
                    cv2.line(display, (x, y + h), (x + tamanho, y + h), cor, 4)
                    cv2.line(display, (x, y + h), (x, y + h - tamanho), cor, 4)

                    # inferior direito
                    cv2.line(display, (x + w, y + h), (x + w - tamanho, y + h), cor, 4)
                    cv2.line(display, (x + w, y + h), (x + w, y + h - tamanho), cor, 4)

                    # FUNDO TEXTO
                    cv2.rectangle(
                        display,
                        (20, 20),
                        (700, 90),
                        (0, 0, 0),
                        -1
                    )

                    # TEXO PLACA
                    cv2.putText(
                        display,
                        f"PLACA: {placa}",
                        (35, 55),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1,
                        cor,
                        3
                    )

                    # STATUS
                    cv2.putText(
                        display,
                        placa_status,
                        (35, 85),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.8,
                        cor,
                        2
                    )

                    break

        _, buffer = cv2.imencode('.jpg', display)
        frame_bytes = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')