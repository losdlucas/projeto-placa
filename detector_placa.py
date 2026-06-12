import cv2
import pytesseract
import re
from database import verificar_placa, salvar_historico

placa_ja_registrada = None

pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Users\49182867801\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"
)


def extrair_placa(texto):

    texto = texto.upper()

    texto = re.sub(r'[^A-Z0-9]', '', texto)

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
        gray,
        255,
        cv2.ADAPTIVE_THRESH_MEAN_C,
        cv2.THRESH_BINARY_INV,
        19,
        9
    )

    kernel = cv2.getStructuringElement(
        cv2.MORPH_RECT,
        (5, 5)
    )

    return cv2.morphologyEx(
        thresh,
        cv2.MORPH_CLOSE,
        kernel
    )


def processar_frame(frame):

    global placa_ja_registrada

    processada = preprocessar(frame)

    contornos, _ = cv2.findContours(
        processada,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    contornos = sorted(
        contornos,
        key=cv2.contourArea,
        reverse=True
    )[:15]

    for contorno in contornos:

        area = cv2.contourArea(contorno)

        if area < 4000:
            continue

        x, y, w, h = cv2.boundingRect(contorno)

        proporcao = w / float(h)

        if not (2.2 < proporcao < 5.5):
            continue

        placa_img = frame[y:y+h, x:x+w]

        placa_proc = preprocessar(placa_img)

        texto = pytesseract.image_to_string(
            placa_proc,
            config='--oem 3 --psm 7'
        )

        placa = extrair_placa(texto)

        if placa:

            if placa != placa_ja_registrada:

                veiculo = verificar_placa(placa)

                if veiculo:
                    status = "ENTRADA AUTORIZADA"
                else:
                    status = "VEICULO NAO ENCONTRADO"

                salvar_historico(
                    placa,
                    status
                )

                placa_ja_registrada = placa

                return placa, status

    return None, None