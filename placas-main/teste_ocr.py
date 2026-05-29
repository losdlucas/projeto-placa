import cv2
import pytesseract

img = cv2.imread("placa.jpg")

if img is None:
    print("❌ Imagem não encontrada!")
    exit()

texto = pytesseract.image_to_string(img)
print(texto)