#pragma once
#ifdef USE_DLNA
#include <freertos/FreeRTOS.h>
#include <freertos/semphr.h>

extern SemaphoreHandle_t g_dlnaHttpMux;

struct DlnaHttpGuard {
  bool ok = false;   // false: a mutex nem szerezhető meg időben -> a hívó ne végezzen HTTP-t
  explicit DlnaHttpGuard(uint32_t timeoutMs = 1500) {
    ok = g_dlnaHttpMux ? (xSemaphoreTake(g_dlnaHttpMux, pdMS_TO_TICKS(timeoutMs)) == pdTRUE) : true;
    _taken = ok && g_dlnaHttpMux;
  }
  ~DlnaHttpGuard() { if (_taken) xSemaphoreGive(g_dlnaHttpMux); }
  DlnaHttpGuard(const DlnaHttpGuard&) = delete;
  DlnaHttpGuard& operator=(const DlnaHttpGuard&) = delete;
private:
  bool _taken = false;
};
#endif