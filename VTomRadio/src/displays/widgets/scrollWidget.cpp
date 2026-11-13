#include "../../core/config.h"
#include "../display_select.h"
#include "widgets.h"
#include "../../core/fonts.h"

ScrollWidget::ScrollWidget(const char* separator, ScrollConfig conf, uint16_t fgcolor, uint16_t bgcolor) {
    init(separator, conf, fgcolor, bgcolor);
}

ScrollWidget::~ScrollWidget() {
    if (_spr) {
        _spr->deleteSprite();
        delete _spr;
    }
    _freeStrip();
    if (_sep) free(_sep);
}

void ScrollWidget::init(const char* separator, ScrollConfig conf, uint16_t fgcolor, uint16_t bgcolor) {

    TextWidget::init(conf.widget, conf.buffsize, conf.uppercase, fgcolor, bgcolor);

    _sep = (char*)malloc(4);
    if (_sep) snprintf(_sep, 4, " %.*s ", 1, separator);

    _startscrolldelay = conf.startscrolldelay;
    _scrolldelta = conf.scrolldelta;
    _scrolltime = conf.scrolltime;
    _width = conf.width;

    _spr = new LGFX_Sprite(&dsp);
    _spr->setColorDepth(16);
    _spr->setPsram(true);

    // 1. ELŐBB beállítjuk a paramétereket (font betöltése), hogy tudjuk a magasságot
    _setTextParams();

    // 2. Lekérjük a tényleges font magasságot (Roboto36 esetén ez ~40-42 px lesz)
    _textheight = _spr->fontHeight();

    // 3. CSAK MOST hozzuk létre a Sprite-ot a pontos mérettel
    if (!_spr->createSprite(_width, _textheight)) {
        // Ha PSRAM-ba nem sikerült, megpróbáljuk belső RAM-ba
        _spr->setPsram(false);
        _spr->createSprite(_width, _textheight);
    }

    _scrollOffset = 0;
    _doscroll = false;
}

void ScrollWidget::_setTextParams() {
    if (!_spr || _config.textsize == 0) return;
    _applyFont(_spr);
}

// (MB) Ta sama czcionka i kolory dla dowolnego sprite'a (ekranowego albo długiego paska)
void ScrollWidget::_applyFont(LGFX_Sprite* _spr) {
    _spr->setTextColor(_fgcolor, _bgcolor);
    _spr->setTextWrap(false);
    _spr->unloadFont();
    if (_config.textsize == 16 && font_vlw_16) {
        _spr->loadFont(font_vlw_16);
        _spr->setTextSize(1);
    } else if (_config.textsize == 18 && font_vlw_18) {
        _spr->loadFont(font_vlw_18);
        _spr->setTextSize(1);

    } else if (_config.textsize == 20 && font_vlw_20) {
        _spr->loadFont(font_vlw_20);
        _spr->setTextSize(1);

    } else if (_config.textsize == 22 && font_vlw_22) {
        _spr->loadFont(font_vlw_22);
        _spr->setTextSize(1);

    } else if (_config.textsize == 24 && font_vlw_24) {
        _spr->loadFont(font_vlw_24);
        _spr->setTextSize(1);
    } else if (_config.textsize == 26 && font_vlw_26) {
        _spr->loadFont(font_vlw_26);
        _spr->setTextSize(1);

    } else if (_config.textsize == 36 && font_vlw_36) {
        _spr->loadFont(font_vlw_36);
        _spr->setTextSize(1);

    } else {
        _spr->setFont(nullptr);
        _spr->setTextSize(2);
    }
}

void ScrollWidget::setFontBySize(uint8_t size) {
    if (!_spr) return;
    _config.textsize = size;
    _setTextParams();
    uint16_t newHeight = _spr->fontHeight();
    if (newHeight != _textheight) {
        _textheight = newHeight;
        _spr->deleteSprite();
        if (!_spr->createSprite(_width, _textheight)) {
            _spr->setPsram(false);
            _spr->createSprite(_width, _textheight);
        }
    }
    _textwidth = _spr->textWidth(_text);
    int sepW = _spr->textWidth(_sep);
    _fullWidth = _textwidth + sepW;
    _doscroll = (_textwidth > _width);
    _freeStrip(); // (MB) nowa czcionka = pasek do narysowania od nowa
    _scrollOffset = 0;
    _scrollState = SCROLL_WAIT_START;
    _scrolldelay = millis();
    if (_active) { _draw(); }
}

void ScrollWidget::setText(const char* txt) {
    if (!txt) return;
    strlcpy(_text, txt, _buffsize - 1);
    if (strcmp(_oldtext, _text) == 0) return;
    _setTextParams();
    _textwidth = _spr->textWidth(_text);
    int sepW = _spr->textWidth(_sep);
    _fullWidth = _textwidth + sepW;
    _doscroll = (_textwidth > _width);
    // (MB) nowy tekst: pasek narysuje się przy pierwszym kroku przewijania; krótki tekst nie potrzebuje paska
    if (_doscroll) _stripDirty = true;
    else _freeStrip();
    _scrollOffset = 0;
    _scrollState = SCROLL_WAIT_START;
    _scrolldelay = millis();
    if (_active) { _draw(); }
    strlcpy(_oldtext, _text, _buffsize);
}

void ScrollWidget::setText(const char* txt, const char* format) {
    if (!txt || !format) return;
    char buf[_buffsize];
    int  n = snprintf(buf, sizeof(buf), format, txt);
    if (n < 0) return;
    buf[sizeof(buf) - 1] = '\0';
    setText(buf);
}

void ScrollWidget::loop() {
    if (_locked || !_active || !_doscroll) return;

    uint32_t now = millis();

    // (MB) Postój na początku tekstu
    if (_scrollState == SCROLL_WAIT_START) {
        if (now - _scrolldelay >= _startscrolldelay) {
            _scrollState = SCROLL_RUN;
            _scrolldelay = now;
        }
        return;
    }

    // (MB) Przesuwanie liczone z upływu czasu: równa prędkość nawet przy spóźnionej klatce
    uint32_t elapsed = now - _scrolldelay;
    if (_scrolltime == 0) {
        // (MB) zabezpieczenie: czas 0 ms = jeden krok w każdej klatce (jak w starym kodzie), bez dzielenia przez zero
        _scrolldelay = now;
        _stepsDue = 1;
        _draw();
        return;
    }
    if (elapsed < _scrolltime) return;
    uint32_t steps = elapsed / _scrolltime;
    if (steps > 4) {
        // po dłuższej przerwie (np. zajęty procesor) nie przeskakuj daleko
        steps = 4;
        _scrolldelay = now;
    } else {
        _scrolldelay += steps * _scrolltime;
    }
    _stepsDue = steps;
    _draw();
}

void ScrollWidget::setColors(uint16_t fg, uint16_t bg) {
    _fgcolor = fg;
    _bgcolor = bg;
    _setTextParams();
    _stripDirty = true; // (MB) nowe kolory = pasek do narysowania od nowa
    _draw();
}

// --- TISZTA TÖRLÉS ---
void ScrollWidget::_clear() {
    // Ellenőrizzük, hogy a Sprite létezik-e és van-e mérete
    if (_spr && _spr->width() > 0) {
        _spr->fillSprite(_bgcolor);
        _spr->pushSprite(_config.left, _config.top);
    } else {
        dsp.fillRect(_config.left, _config.top, _width, _textheight, _bgcolor);
    }
}

void ScrollWidget::_draw() {
    if (!_active || _locked || !_spr || _spr->width() <= 0) return;
    //  --- 1. ESET: NINCS GÖRGETÉS (Rövid szöveg) ---
    if (!_doscroll) {
        _spr->fillSprite(_bgcolor);
        int16_t startX = 0;

        if (_config.align == WA_CENTER) {
            startX = (_width - _textwidth) / 2;
        } else if (_config.align == WA_RIGHT) {
            startX = _width - _textwidth;
        }

        _spr->setCursor(startX, 0);
        _spr->print(_text);
        _spr->pushSprite(_config.left, _config.top);
        return;
    }

    // --- 2. ESET: VÁRAKOZÁS A GÖRGETÉS ELŐTT ---
    if (_scrollState == SCROLL_WAIT_START) {
        // Ha még 0 az offset, rajzoljuk ki az elejét álló helyzetben
        if (_scrollOffset == 0) {
            _spr->fillSprite(_bgcolor);
            _spr->setCursor(0, 0);
            _spr->print(_text);
            _spr->pushSprite(_config.left, _config.top);
        }

        // Időellenőrzés: Csak akkor lépünk tovább, ha letelt a várakozás
        if (millis() - _scrolldelay >= _startscrolldelay) {
            _scrollState = SCROLL_RUN;
            _scrolldelay = millis(); // Reseteljük az időzítőt a folyamatos gördüléshez
        }
        return;
    }

    // --- 3. ESET: AKTÍV GÖRGETÉS (SCROLL_RUN) ---
    if (_scrollState == SCROLL_RUN) {
        // Offset növelése
        _scrollOffset += _scrolldelta * _stepsDue; // (MB) 0 = tylko odśwież (np. zmiana kolorów)
        _stepsDue = 0;

        // Ha végére értünk a teljes hossznak (szöveg + separator)
        if (_scrollOffset >= _fullWidth) {
            _scrollOffset = 0;
            _scrollState = SCROLL_WAIT_START;
            _scrolldelay = millis(); // Itt indul a 2 másodperces várakozás az elején

            // Kirajzoljuk az alapállapotot, hogy ne maradjon üres vagy félkész a kép
            _spr->fillSprite(_bgcolor);
            _spr->setCursor(0, 0);
            _spr->print(_text);
            _spr->pushSprite(_config.left, _config.top);
            return;
        }

        // (MB) Wariant B: kopiujemy okienko z gotowego paska zamiast rysować litery od nowa
        if (_prepareStrip()) {
            const int       h = _spr->height();
            const uint32_t  dstStride = _spr->bufferLength() / h;     // bajty na wiersz
            const uint32_t  srcStride = _strip->bufferLength() / h;
            const int       first = min(_width, (uint16_t)(_fullWidth - _scrollOffset)); // piksele do końca paska
            uint8_t*        dst = (uint8_t*)_spr->getBuffer();
            const uint8_t*  src = (const uint8_t*)_strip->getBuffer();
            for (int y = 0; y < h; y++) {
                uint8_t*       d = dst + y * dstStride;
                const uint8_t* srow = src + y * srcStride;
                memcpy(d, srow + _scrollOffset * 2, first * 2);
                if (first < _width) memcpy(d + first * 2, srow, (_width - first) * 2); // początek napisu wjeżdża z prawej
            }
            _spr->pushSprite(_config.left, _config.top);
            return;
        }

        // Rajzolás folyamata (zapas: gdy pasek się nie zmieścił w pamięci, rysujemy jak dawniej)
        _spr->fillSprite(_bgcolor);

        // Első példány kirajzolása (balra csúszik ki)
        _spr->setCursor(-_scrollOffset, 0);
        _spr->print(_text);
        _spr->print(_sep);

        // Második példány kirajzolása (jobbról úszik be)
        // Csak akkor rajzoljuk, ha az első már elkezdett kimenni a képből
        if (_scrollOffset > 0) {
            _spr->setCursor(_fullWidth - _scrollOffset, 0);
            _spr->print(_text);
            _spr->print(_sep);
        }

        _spr->pushSprite(_config.left, _config.top);
        // (MB) czas następnego kroku liczy teraz loop()
    }
}
void ScrollWidget::setActive(bool act, bool clr) {
    // 1. Alaphelyzetbe állítjuk a belső változókat, mielőtt bármi történne
    if (act) {
        _scrollOffset = 0;
        _scrollState = SCROLL_WAIT_START;
        _scrolldelay = millis();
        if (_spr && _spr->width() > 0) {
            _spr->fillSprite(_bgcolor); // Megelőzzük a szellemképet
        }
    }

    // 2. Meghívjuk az ősosztály metódusát.
    Widget::setActive(act, clr);
}

void ScrollWidget::_reset() {
    _scrolldelay = millis();
    _scrollOffset = 0;
    _scrollState = SCROLL_WAIT_START;
    if (_spr && _spr->width() > 0) _spr->fillSprite(_bgcolor);
}

// (MB) Wariant B: przygotuj długi pasek z całym napisem i separatorem (rysowany raz na zmianę tekstu)
bool ScrollWidget::_prepareStrip() {
    if (!_spr || _fullWidth <= _width || _textheight == 0) return false;
    if (_spr->getColorDepth() != 16) return false;
    if (_strip && !_stripDirty && _strip->width() == _fullWidth && _strip->height() == _spr->height()) return true;

    if (!_strip) {
        _strip = new LGFX_Sprite(&dsp);
        _strip->setColorDepth(16);
        _strip->setPsram(true); // tylko PSRAM: małej RAM nie ruszamy
    }
    if (_strip->width() != _fullWidth || _strip->height() != _spr->height()) {
        _strip->deleteSprite();
        if (!_strip->createSprite(_fullWidth, _spr->height())) {
            _freeStrip();
            return false;
        }
    }
    _applyFont(_strip);
    _strip->fillSprite(_bgcolor);
    _strip->setCursor(0, 0);
    _strip->print(_text);
    _strip->print(_sep);
    _strip->unloadFont(); // czcionka zajmuje małą RAM, pasek już jej nie potrzebuje
    _stripDirty = false;
    return true;
}

void ScrollWidget::_freeStrip() {
    if (_strip) {
        _strip->deleteSprite();
        delete _strip;
        _strip = nullptr;
    }
    _stripDirty = true;
}
