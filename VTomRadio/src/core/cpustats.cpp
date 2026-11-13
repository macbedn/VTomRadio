// (MB) Pomiar obciążenia rdzeni ESP32: strona http://<IP radia>/cpu
// Włączane przez #define CPU_STATS w myoptions.h.
// Radio mierzy samo co 2 s w tle, strona pokazuje ostatni wynik.
#include "options.h"
#ifdef CPU_STATS
#    include "Arduino.h"
#    include "cpustats.h"
#    include <freertos/FreeRTOS.h>
#    include <freertos/task.h>
#    include <esp_heap_caps.h>

namespace {
    constexpr int MAX_TASKS = 48;
    struct PrevEntry {
        TaskHandle_t handle;
        uint32_t     counter;
    };
    PrevEntry prev[MAX_TASKS];
    int       prevCount = 0;
    uint32_t  prevTotal = 0;
    bool      havePrev = false;

    uint32_t findPrev(TaskHandle_t h, bool& found) {
        for (int i = 0; i < prevCount; i++) {
            if (prev[i].handle == h) {
                found = true;
                return prev[i].counter;
            }
        }
        found = false;
        return 0;
    }

    String            lastReport = "Pomiar jeszcze trwa, odswiez za 2 sekundy.\n";
    SemaphoreHandle_t reportMutex = nullptr;

    String buildReport() {
        static TaskStatus_t tasks[MAX_TASKS];
        uint32_t            total = 0;
        UBaseType_t         n = uxTaskGetSystemState(tasks, MAX_TASKS, &total);

        String out;
        out.reserve(2048);
        char line[96];

        if (!havePrev) {
            out += "Pierwszy pomiar zapamietany, odswiez za 2 sekundy.\n";
        } else {
            uint32_t dt = total - prevTotal; // mikrosekundy od poprzedniego odswiezenia
            if (dt == 0) dt = 1;

            // bezczynnosc rdzeni = czas zadan IDLE0 / IDLE1
            uint32_t idle[2] = {0, 0};
            for (UBaseType_t i = 0; i < n; i++) {
                bool     f;
                uint32_t p = findPrev(tasks[i].xHandle, f);
                if (!f) continue;
                if (strcmp(tasks[i].pcTaskName, "IDLE0") == 0) idle[0] = tasks[i].ulRunTimeCounter - p;
                if (strcmp(tasks[i].pcTaskName, "IDLE1") == 0) idle[1] = tasks[i].ulRunTimeCounter - p;
            }
            snprintf(line, sizeof(line), "Okres pomiaru: %.1f s\n\n", dt / 1000000.0f);
            out += line;
            for (int c = 0; c < 2; c++) {
                float busy = 100.0f - (idle[c] * 100.0f / dt);
                if (busy < 0) busy = 0;
                snprintf(line, sizeof(line), "Rdzen %d: %5.1f %% zajety\n", c, busy);
                out += line;
            }
            out += "\nZadanie            rdzen  % jednego rdzenia\n";
            out += "-------------------------------------------\n";
            // od najbardziej zajetych
            bool used[MAX_TASKS] = {false};
            for (UBaseType_t k = 0; k < n; k++) {
                int      best = -1;
                uint32_t bestD = 0;
                for (UBaseType_t i = 0; i < n; i++) {
                    if (used[i]) continue;
                    bool     f;
                    uint32_t p = findPrev(tasks[i].xHandle, f);
                    uint32_t d = f ? tasks[i].ulRunTimeCounter - p : 0;
                    if (best < 0 || d > bestD) {
                        best = i;
                        bestD = d;
                    }
                }
                if (best < 0) break;
                used[best] = true;
                float pct = bestD * 100.0f / dt;
                if (pct < 0.05f) continue; // pomijamy zadania prawie bez pracy
                int core = tasks[best].xCoreID;
                snprintf(line, sizeof(line), "%-18s %5s  %5.1f\n", tasks[best].pcTaskName,
                         (core == 0 || core == 1) ? (core == 0 ? "0" : "1") : "oba", pct);
                out += line;
            }
        }

        snprintf(line, sizeof(line), "\nWolna RAM: %u B (najmniej od startu: %u B)\n",
                 (unsigned)heap_caps_get_free_size(MALLOC_CAP_INTERNAL),
                 (unsigned)heap_caps_get_minimum_free_size(MALLOC_CAP_INTERNAL));
        out += line;
        snprintf(line, sizeof(line), "Wolna PSRAM: %u B\n", (unsigned)heap_caps_get_free_size(MALLOC_CAP_SPIRAM));
        out += line;

        // zapamietaj stan do nastepnego odswiezenia
        prevCount = 0;
        for (UBaseType_t i = 0; i < n && prevCount < MAX_TASKS; i++) {
            prev[prevCount].handle = tasks[i].xHandle;
            prev[prevCount].counter = tasks[i].ulRunTimeCounter;
            prevCount++;
        }
        prevTotal = total;
        havePrev = true;
        return out;
    }

    void statsTask(void*) {
        while (true) {
            String r = buildReport();
            xSemaphoreTake(reportMutex, portMAX_DELAY);
            lastReport = r;
            xSemaphoreGive(reportMutex);
            vTaskDelay(pdMS_TO_TICKS(2000));
        }
    }

    void handleCpu(AsyncWebServerRequest* request) {
        xSemaphoreTake(reportMutex, portMAX_DELAY);
        String r = lastReport;
        xSemaphoreGive(reportMutex);
        request->send(200, "text/plain; charset=utf-8", r);
    }
} // namespace

void cpustats_register(AsyncWebServer& server) {
    reportMutex = xSemaphoreCreateMutex();
    xTaskCreatePinnedToCore(statsTask, "cpustats", 4096, nullptr, 1, nullptr, 0);
    server.on("/cpu", HTTP_GET, handleCpu);
}
#endif
