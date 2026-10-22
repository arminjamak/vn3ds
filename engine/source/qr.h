#pragma once
#include "common.h"

/* QR codes (ISO 18004) for the receive screen's link: byte mode, error
 * correction level M, versions 1 to 10 (up to 213 bytes of text). */
#define QR_MAX_SIZE 57   /* modules per side at version 10 */

/* Encodes text into out (size * size modules, row by row, 1 = dark).
 * Returns the size (21, 25, ...), or 0 if the text is too long. mask -1
 * picks the mask with the lowest penalty, as the standard says; 0-7 forces
 * one (tests). */
int qr_encode(const char *text, int mask, u8 out[QR_MAX_SIZE * QR_MAX_SIZE]);
