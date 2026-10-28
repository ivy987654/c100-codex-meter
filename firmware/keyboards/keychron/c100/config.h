/* Copyright 2026 @ Keychron (https://www.keychron.com)
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program. If not, see <http://www.gnu.org/licenses/>.
 */

#pragma once
#include "eeconfig_kb.h"

/* SNLED27351 Driver Configuration */
#if defined(RGB_MATRIX_ENABLE)
#    define SPI_DRIVER SPID1
#    define SPI_SCK_PIN A5
#    define SPI_MOSI_PIN A7
#    define SNLED27351_SDB_PIN B7
#    define SNLED27351_SELECT_PINS \
        { A8, C9 }
#    define SNLED27351_SPI_DIVISOR 64
// C100 uses all four RGB current-sink banks (CB1..CB12). Nine-channel
// scanning disables CB10/CB11/CB12 and leaves 30 of the 100 keys dark.
#    define SNLED27351_PHASE_CHANNEL SNLED27351_SCAN_PHASE_12_CHANNEL

/* LED Current Configuration */
#    define SNLED27351_CURRENT_TUNE \
        { 0x86, 0x86, 0x86, 0x86, 0x86, 0x86, 0x86, 0x86, 0x86, 0x86, 0x86, 0x86 }

/* RGB Matrix Configuration */
#    define RGB_MATRIX_LED_COUNT 100
#endif

/* Custom keycodes */
#define CUSTOM_KEYCODES_ENABLE
