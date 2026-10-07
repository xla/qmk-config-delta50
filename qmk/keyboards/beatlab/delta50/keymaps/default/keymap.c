// SPDX-License-Identifier: GPL-2.0-or-later
// New authored defaults. This is not a reconstruction of the factory firmware.
#include QMK_KEYBOARD_H

enum delta50_layers { BASE, NAV, NUM, FN };

// Each LAYOUT row follows the physical board, not the electrical matrix.
// The last keys of physical rows 0/1/2 are matrix [1,13]/[2,13]/[3,13].
const uint16_t PROGMEM keymaps[][MATRIX_ROWS][MATRIX_COLS] = {
    [BASE] = LAYOUT(
        TG(NUM), KC_ESC,         KC_Q,    KC_W,    KC_E,    KC_R,    KC_T,    KC_Y,    KC_U,    KC_I,    KC_O,    KC_P,    KC_LBRC, KC_RBRC, KC_BSPC,
        KC_NO,   LCTL_T(KC_TAB), KC_A,    KC_S,    KC_D,    KC_F,    KC_G,    KC_H,    KC_J,    KC_K,    KC_L,    KC_SCLN, KC_QUOT, KC_ENT,
        KC_NO,   KC_LSFT,        KC_Z,    KC_X,    KC_C,    KC_V,    KC_B,    KC_N,    KC_M,    KC_COMM, KC_DOT,  KC_SLSH, KC_RSFT, MO(NAV),
        KC_NO,                  KC_LALT, KC_LGUI,                   KC_SPC,          KC_SPC,           MO(NAV), MO(FN)
    ),
    [NAV] = LAYOUT(
        _______, KC_GRV,        KC_1,    KC_2,    KC_3,    KC_4,    KC_5,    KC_6,    KC_7,    KC_8,    KC_9,    KC_0,    KC_MINS, KC_EQL,  KC_DEL,
        _______, _______,       KC_HOME, KC_PGDN, KC_PGUP, KC_END,  _______, KC_LEFT, KC_DOWN, KC_UP,   KC_RGHT, _______, KC_BSLS, _______,
        _______, _______,       _______, _______, _______, _______, _______, _______, _______, _______, _______, _______, _______, _______,
        _______,                _______, _______,                   _______,         _______,          _______, _______
    ),
    [NUM] = LAYOUT(
        TG(NUM), _______,       KC_1,    KC_2,    KC_3,    KC_4,    KC_5,    KC_6,    KC_7,    KC_8,    KC_9,    KC_0,    KC_MINS, KC_EQL,  _______,
        _______, _______,       _______, _______, _______, _______, _______, _______, _______, _______, _______, _______, KC_BSLS, _______,
        _______, _______,       _______, _______, _______, _______, _______, _______, _______, _______, _______, _______, _______, _______,
        _______,                _______, _______,                   _______,         _______,          _______, _______
    ),
    [FN] = LAYOUT(
        _______, _______,       KC_F1,   KC_F2,   KC_F3,   KC_F4,   KC_F5,   KC_F6,   KC_F7,   KC_F8,   KC_F9,   KC_F10,  KC_F11,  KC_F12,  _______,
        _______, _______,       UG_TOGG, UG_NEXT, UG_HUEU, UG_SATU, UG_VALU, KC_MPRV, KC_VOLD, KC_VOLU, KC_MNXT, KC_MPLY, KC_MUTE, _______,
        _______, _______,       _______, UG_PREV, UG_HUED, UG_SATD, UG_VALD, _______, _______, _______, _______, _______, _______, _______,
        _______,                _______, _______,                   _______,         _______,          _______, _______
    )
};
