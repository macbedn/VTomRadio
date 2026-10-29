#pragma once

#include <stdint.h>
#include "common.h"

void inputSelect_drawScreen(uint8_t selected);
uint8_t inputSelect_moveSelection(uint8_t selected, int delta);
uint8_t inputSelect_normalizeSelection(uint8_t selected);
