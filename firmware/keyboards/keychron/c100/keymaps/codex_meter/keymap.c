/* Keychron C100 - full-screen RGB flow with Codex remaining-usage highlights. */
#include QMK_KEYBOARD_H
#include "color.h"

extern HSV per_key_led[RGB_MATRIX_LED_COUNT];

const uint16_t PROGMEM keymaps[][MATRIX_ROWS][MATRIX_COLS] = {
    [0] = LAYOUT_ortho_10x10(
        KC_NO, KC_NO, KC_NO, KC_NO, KC_NO, KC_NO, KC_NO, KC_NO, KC_NO, KC_NO,
        KC_NO, KC_NO, KC_NO, KC_NO, KC_NO, KC_NO, KC_NO, KC_NO, KC_NO, KC_NO,
        KC_NO, KC_NO, KC_NO, KC_NO, KC_NO, KC_NO, KC_NO, KC_NO, KC_NO, KC_NO,
        KC_NO, KC_NO, KC_NO, KC_NO, KC_NO, KC_NO, KC_NO, KC_NO, KC_NO, KC_NO,
        KC_NO, KC_NO, KC_NO, KC_NO, KC_NO, KC_NO, KC_NO, KC_NO, KC_NO, KC_NO,
        KC_NO, KC_NO, KC_NO, KC_NO, KC_NO, KC_NO, KC_NO, KC_NO, KC_NO, KC_NO,
        KC_NO, KC_NO, KC_NO, KC_NO, KC_NO, KC_NO, KC_NO, KC_NO, KC_NO, KC_NO,
        KC_NO, KC_NO, KC_NO, KC_NO, KC_NO, KC_NO, KC_NO, KC_NO, KC_NO, KC_NO,
        KC_NO, KC_NO, KC_NO, KC_NO, KC_NO, KC_NO, KC_NO, KC_NO, KC_NO, KC_NO,
        KC_NO, KC_NO, KC_NO, KC_NO, KC_NO, KC_NO, KC_NO, KC_NO, KC_NO, KC_NO
    ),
};

void keyboard_post_init_user(void) {
    rgb_matrix_enable_noeeprom();
    for (uint8_t i = 0; i < RGB_MATRIX_LED_COUNT; i++) {
        per_key_led[i] = (HSV){0, 0, 0};
    }
}

bool rgb_matrix_indicators_user(void) {
    uint8_t phase = (uint8_t)(timer_read32() / 18);

    for (uint8_t i = 0; i < RGB_MATRIX_LED_COUNT; i++) {
        /* Driver order is column-major from right to left. Convert it back to
         * the user's front-view 10x10 grid to make a diagonal RGB flow. */
        uint8_t row = i % 10;
        uint8_t col = 9 - (i / 10);

        /* The host stores the quota mask in per_key_led[].v. Remaining keys
         * are bright; consumed keys stay dim so the whole board keeps flowing. */
        uint8_t value = per_key_led[i].v > 0 ? 205 : 28;
        HSV hsv = {
            .h = phase + col * 13 + row * 6,
            .s = 255,
            .v = value,
        };
        RGB rgb = hsv_to_rgb(hsv);
        rgb_matrix_set_color(i, rgb.r, rgb.g, rgb.b);
    }
    return false;
}
