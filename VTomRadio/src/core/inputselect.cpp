#include "inputselect.h"

#include "options.h"

#if DSP_MODEL != DSP_DUMMY
#include <Arduino.h>
#include "config.h"
#include "fonts.h"
#include "../displays/display_select.h"

namespace {

LGFX_Sprite* inputSelectCanvas = nullptr;
uint16_t inputSelectWidth = 0;
uint16_t inputSelectHeight = 0;

static uint8_t getInputOptions(inputSource_e* sources, const char** labels) {
    uint8_t count = 0;
    sources[count] = INPUT_WEB;
    labels[count++] = "WEB radio";
#ifdef USE_SD
    sources[count] = INPUT_SD;
    labels[count++] = "SD card";
#endif
#ifdef USE_DLNA
    if (LittleFS.exists(PLAYLIST_DLNA_PATH)) {
        sources[count] = INPUT_DLNA;
        labels[count++] = "DLNA";
    }
#endif
    return count;
}

static bool ensureInputSelectCanvas(uint16_t width, uint16_t height) {
    if (inputSelectCanvas && inputSelectWidth == width && inputSelectHeight == height) { return true; }
    if (inputSelectCanvas) {
        inputSelectCanvas->deleteSprite();
        delete inputSelectCanvas;
        inputSelectCanvas = nullptr;
    }

    inputSelectCanvas = new LGFX_Sprite(&dsp);
    inputSelectCanvas->setColorDepth(16);
    inputSelectCanvas->setPsram(true);
    if (!inputSelectCanvas->createSprite(width, height)) {
        inputSelectCanvas->setPsram(false);
        if (!inputSelectCanvas->createSprite(width, height)) {
            Serial.println("[INPUT] Failed to allocate selector display sprite");
            delete inputSelectCanvas;
            inputSelectCanvas = nullptr;
            return false;
        }
    }

    inputSelectWidth = width;
    inputSelectHeight = height;
    inputSelectCanvas->setTextDatum(middle_center);
    return true;
}

static void loadRoboto(uint8_t size) {
    inputSelectCanvas->unloadFont();
    uint8_t* font = nullptr;
    switch (size) {
        case 18: font = font_vlw_18; break;
        case 20: font = font_vlw_20; break;
        case 26: font = font_vlw_26; break;
        case 36: font = font_vlw_36; break;
        default: break;
    }
    if (font) {
        inputSelectCanvas->loadFont(font);
        inputSelectCanvas->setTextSize(1);
    } else {
        inputSelectCanvas->setFont(nullptr);
        inputSelectCanvas->setTextSize(size >= 30 ? 3 : size >= 18 ? 2 : 1);
    }
}

} // namespace

void inputSelect_drawScreen(uint8_t selected) {
    const uint16_t width = dsp.width();
    const uint16_t height = dsp.height();
    inputSource_e sources[4];
    const char* labels[4];
    const uint8_t count = getInputOptions(sources, labels);
    if (!ensureInputSelectCanvas(width, height)) { return; }

    const int16_t margin = width < 280 ? 10 : 16;
    const int16_t headerHeight = height < 260 ? 40 : 48;
    const int16_t headerFontSize = width >= 400 ? 36 : 26;
    const int16_t columnWidth = min<int16_t>(width - margin * 2, 360);
    const int16_t columnX = (width - columnWidth) / 2;
    const int16_t listTop = headerHeight + 20;
    const int16_t listBottom = height - 10;
    const int16_t rowGap = height < 260 ? 7 : 10;
    const int16_t rowHeight = (listBottom - listTop - rowGap * 3) / 4;
    const int16_t firstRowTop = headerHeight + rowHeight / 2;

    LGFX_Sprite& canvas = *inputSelectCanvas;
    canvas.fillScreen(config.theme.background);

    canvas.fillRect(0, 0, width, headerHeight, config.theme.metabg);
    loadRoboto(headerFontSize);
    canvas.setTextColor(config.theme.prst_title1);
    canvas.setTextDatum(top_left);
    const char* header = "Input select";
    const int16_t headerTextWidth = canvas.textWidth(header);
    const int16_t headerTextHeight = canvas.fontHeight();
    canvas.drawString(header, (width - headerTextWidth) / 2, (headerHeight - headerTextHeight) / 2);
    canvas.drawFastHLine(0, headerHeight - 1, width, config.theme.prst_line);

    loadRoboto(20);
    canvas.setTextDatum(top_left);
    for (uint8_t i = 0; i < count; ++i) {
        const int16_t top = firstRowTop + i * (rowHeight + rowGap);
        const bool active = sources[i] == selected;
        const uint16_t background = active ? config.theme.prst_accent : config.theme.prst_card;
        const uint16_t text = active ? config.theme.prst_title1 : config.theme.prst_title3;

        canvas.fillRoundRect(columnX, top, columnWidth, rowHeight, 10, background);
        canvas.drawRoundRect(columnX, top, columnWidth, rowHeight, 10, config.theme.prst_line);
        canvas.setTextColor(text);
        const int16_t textWidth = canvas.textWidth(labels[i]);
        const int16_t textHeight = canvas.fontHeight();
        canvas.drawString(labels[i], (width - textWidth) / 2, top + (rowHeight - textHeight) / 2);
    }

    canvas.unloadFont();
    canvas.pushSprite(0, 0);
}

uint8_t inputSelect_moveSelection(uint8_t selected, int delta) {
    if (delta == 0) { return selected; }
    inputSource_e sources[4];
    const char* labels[4];
    const uint8_t count = getInputOptions(sources, labels);
    uint8_t position = 0;
    bool selectedFound = false;
    for (uint8_t i = 0; i < count; ++i) {
        if (sources[i] == selected) {
            position = i;
            selectedFound = true;
            break;
        }
    }
    if (!selectedFound) { return sources[delta > 0 ? 1 % count : count - 1]; }
    if (delta > 0) {
        position = (position + 1) % count;
    } else {
        position = (position + count - 1) % count;
    }
    return sources[position];
}

uint8_t inputSelect_normalizeSelection(uint8_t selected) {
    inputSource_e sources[4];
    const char* labels[4];
    const uint8_t count = getInputOptions(sources, labels);
    for (uint8_t i = 0; i < count; ++i) {
        if (sources[i] == selected) { return selected; }
    }
    return sources[0];
}
#else
void inputSelect_drawScreen(uint8_t) {}
uint8_t inputSelect_moveSelection(uint8_t selected, int) { return selected; }
uint8_t inputSelect_normalizeSelection(uint8_t selected) { return selected; }
#endif
