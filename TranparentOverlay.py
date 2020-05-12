import cv2


def transparentOverlay(src, overlay, pos=(0, 0), scale=1):
    """
    :param src: Input Color Background Image
    :param overlay: transparent Image (BGRA)
    :param pos:  position where the image to be blit.
    :param scale : scale factor of transparent image.
    :return: Resultant Image
    """
    overlay = cv2.resize(overlay, (0, 0), fx=scale, fy=scale)
    h, w, _ = overlay.shape  # Size of foreground

    rows, cols, _ = src.shape  # Size of background Image
    x, y = pos[0], pos[1]  # Position of foreground/overlay image
    x -= w//2

    background = src[y:min(y+h, rows), x:min(x+w, cols)]
    b_h, b_w, _ = background.shape
    if b_h <= 0 or b_w <= 0:
        return src
    foreground = overlay[0:b_h, 0:b_w]
    alpha = foreground[:, :, 3].astype(float)
    alpha = cv2.merge([alpha, alpha, alpha])
    if alpha is None:
        print ("Debuf")
    alpha = alpha/255.0

    foreground = foreground.astype(float)
    background = background.astype(float)

    foreground = cv2.multiply(alpha, foreground[:,:,:3])
    background = cv2.multiply(1.0 - alpha, background)
    outImage = cv2.add(foreground, background).astype("uint8")

    src[y:y+b_h, x:x+b_w] = outImage
    return src

